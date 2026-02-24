import subprocess
import logging
import tempfile
import shutil
import os
from rq import get_current_job
from django_rq import job
from django.conf import settings as django_settings
from .models import Docking, Protein, Ligand, User, Job
from rq import get_current_job as get_rq_job

logging.basicConfig(filename='script_output.log', level=logging.DEBUG)


# 1. FUNCIÓN GLOBAL HELPER: run_script
# Se define AFUERA para que sea accesible sin importar los bloques try/except
def run_script(cmd, django_job=None):
    home_dir = os.path.expanduser("~")
    print(f"DEBUG: Ejecutando comando: {' '.join(cmd)}", flush=True)

    # Preparamos el entorno con las variables que tus scripts esperan
    custom_env = os.environ.copy()
    custom_env["HOMEDIR"] = home_dir
    # Aprovechamos para asegurar SCRIPTDIR también
    if not "SCRIPTDIR" in custom_env:
        custom_env["SCRIPTDIR"] = getattr(django_settings, 'SCRIPTDIR', "/home/fabio-noriega/.local/src/jimag-scripts")
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Une errores con salida normal
            universal_newlines=True,
            bufsize=1,
            env=custom_env
        )

        for line in iter(process.stdout.readline, ''):
            clean_line = line.strip()
            if clean_line:
                print(f"BASH_LOG: {clean_line}", flush=True)
                if django_job:
                    #django_job.meta['progress'] = clean_line
                    django_job.progress = clean_line[:200]
                    django_job.save()

        process.stdout.close()
        return_code = process.wait()

        if return_code != 0:
            print(f"DEBUG: El script terminó con código de error {return_code}", flush=True)
        return return_code == 0

    except Exception as e:
        print(f"ERROR CRITICO lanzando subprocess: {e}", flush=True)
        return False

# 2. FUNCIÓN GLOBAL HELPER: update_setting
def update_setting(cmd, flag, value):
    if flag in cmd:
        index = cmd.index(flag)
        cmd[index+1] = value
    else:
        cmd.extend([flag, value])


# 3. LA TAREA PRINCIPAL
@job
def run_docking_script(user_id, job_id, docking_settings):
    print(f"DEBUG: Starting task for user {user_id}", flush=True)
    logger = logging.getLogger(__name__)

    try:
        django_job = Job.objects.get(id=job_id)
        django_job.status = 'started'
        django_job.save()
    except Job.DoesNotExist:
        print(f"ERROR: Job {job_id} not found in database.", flush=True)
        return "Job no encontrado en la base de datos"
    
    

    # --- INICIALIZACIÓN Y VALIDACIÓN DEL JOB ---
    try:
        rq_worker_job = get_rq_job()
        print(f"DEBUG: RQ Task ID: {rq_worker_job.id if rq_worker_job else 'None'}", flush=True)
    except Exception as e:
        print(f"CRASH en get_current_job: {e}", flush=True)
        return "Error al obtener job"

    print("\n\n!!! JOB HAS STARTED IN THE WORKER !!!\n\n", flush=True)
    
    prot_file = docking_settings.get('clean_protein_filename', 'PATH_NOT_DEFINED')
    print(f"DEBUG: Attempting to locate protein at: {prot_file}", flush=True)

    if prot_file != 'PATH_NOT_DEFINED':
        if not os.path.exists(prot_file):
             print(f"WARNING: Protein file not physically found at {prot_file}", flush=True)
             logger.error("PROTEIN FILE NOT FOUND!")

    # --- PREPARACIÓN DEL ENTORNO ---
    print("DEBUG: Preparing execution environment...", flush=True)
    try:
        s_dir = getattr(django_settings, 'SCRIPTDIR', None)
        p_root = getattr(django_settings, 'PROJECTROOT', getattr(django_settings, 'BASE_DIR', None))
        
        if not s_dir:
            raise AttributeError("CRITICAL ERROR: 'SCRIPTDIR' is not defined in settings.py or environment variables.")
        if not p_root:
            raise AttributeError("CRITICAL ERROR: Neither 'PROJECTROOT' nor 'BASE_DIR' are defined in settings.py.")

        script_path = f"{s_dir}/multi.sh"
        working_dir = f"{p_root}/media/user_{user_id}/job_{job_id}"
        input_dir = f"{working_dir}/input"
        
        print(f"DEBUG: script_path configurado en: {script_path}", flush=True)
        print(f"DEBUG: working_dir configurado en: {working_dir}", flush=True)

        os.makedirs(working_dir, exist_ok=True)
        os.makedirs(input_dir, exist_ok=True)

        if not os.path.exists(script_path):
            raise FileNotFoundError(f"CRITICAL ERROR: Script not found at {script_path}")
        
        # Mover archivos si hubo pre-procesamiento
        if docking_settings.get('preproc_done'):
            print("DEBUG: Copying pre-processed files...", flush=True)
            if 'pockets_filename' in docking_settings and os.path.exists(docking_settings['pockets_filename']):
                shutil.copy(docking_settings['pockets_filename'], f"{working_dir}/receptor.pdb_predictions.csv")
            if 'clean_protein_filename' in docking_settings and os.path.exists(docking_settings['clean_protein_filename']):
                shutil.copy(docking_settings['clean_protein_filename'], f"{working_dir}/receptor.pdb")

        # Construcción del comando inicial
        script_command = [
            script_path, 
            "--input", input_dir, 
            "--wd", working_dir,
            "--vinalvl", str(docking_settings.get('exhaustiveness', 8)), 
            "--num_modes", str(docking_settings.get('num_modes', 9)), 
            "--run_mode", "predock"
        ]
        
        if docking_settings.get('chains'):
            script_command.extend(["--chains", docking_settings['chains']])
        if docking_settings.get('pockets'):
            script_command.extend([docking_settings['pockets']['option'], docking_settings['pockets']['value']])
        if docking_settings.get('preproc_done') is True:
            script_command.extend(["--preproc_done"])

        print(f"DEBUG: Command ready: {' '.join(script_command)}", flush=True)

    
    except Exception as e:
        print(f"FATAL CRASH during preparation: {e}", flush=True)
        #import traceback
        #traceback.print_exc()
        django_job.status = 'failed'
        django_job.save()
        return "Error in preparation"
    

    

    # --- EJECUCIÓN DEL PREDOCKING ---
    try:
        print(f"DEBUG: Launching PREDOCK run_script...", flush=True)
        # Assuming run_script is a helper function you have defined elsewhere
        if not run_script(script_command, django_job):
            print("DEBUG: Preprocessing run_script returned False", flush=True)
            django_job.status = 'failed'
            django_job.save()
            return "Preprocessing failed"

        pockets_path = os.path.join(working_dir, "pockets")
        #if not os.path.exists(pockets_path):
            #error_msg = f"ERROR: File {pockets_path} was not generated by the script."
            #print(error_msg, flush=True)
            #job.meta['progress'] = error_msg
            #job.save_meta()
            #return "Failed - No pockets file"
        if not os.path.exists(pockets_path):
            django_job.status = 'failed'
            django_job.save()
            return "Failed - No pockets file"

        with open(pockets_path, 'r') as pockets_file:
            pocket_str = pockets_file.readline().strip()
            
        print(f"DEBUG: Pockets read successfully: {pocket_str}", flush=True)

    except Exception as e:
         print(f"CRASH in Predocking: {e}", flush=True)
         return "Predocking Crash"

    # --- CICLO DE DOCKING (LOS RUNS) ---
    print("DEBUG: Entering docking runs loop", flush=True)
    try:
        # 1. Obtenemos las instancias necesarias una sola vez
        p = Protein.objects.get(job_id=job_id)
        l = Ligand.objects.get(job_id=job_id)
        
        # 2. CREAMOS EL DOCKING PRIMERO (La Solución Elegante)
        # Usamos las variables que ya tienes definidas
        docking = Docking.objects.create(
            user=User.objects.get(id=user_id),
            job=django_job,
            protein=p,
            ligand=l,
            pockets=pocket_str
        )
        
        # Actualizamos las relaciones
        p.docking, l.docking = docking.id, docking.id
        p.save()
        l.save()

        # 3. DEFINIMOS LA RUTA DE SALIDA CON EL ID REAL
        docking_id = str(docking.id)
        output_dir = os.path.join("/app/media/user_1/job_" + str(job_id), f"docking_{docking_id}")
        os.makedirs(output_dir, exist_ok=True)

        # 4. ACTUALIZAMOS script_command (Manteniendo el nombre de la variable)
        # Limpiamos y reconfiguramos para el docking real
        script_command = [
            script_path, 
            "--input", input_dir, 
            "--wd", working_dir,
            "--output", output_dir, # Usamos la carpeta con el ID
            "--vinalvl", str(docking_settings.get('exhaustiveness', 8)), 
            "--num_modes", str(docking_settings.get('num_modes', 9)), 
            "--run_mode", "dock_only",
            "--pockets", pocket_str
        ]

        # 5. EJECUTAMOS EL DOCKING UNA SOLA VEZ (Sin el bucle for innecesario)
        print(f"DEBUG: Launching Elegant Docking Run: {' '.join(script_command)}", flush=True)
        
        if not run_script(script_command, django_job):
            django_job.status = 'failed'
            django_job.save()
            return "Docking failed"

        # FINALIZACIÓN EXITOSA
        django_job.status = 'finished'
        django_job.save()
        return "Script completed successfully"

    except Exception as e:
        error_info = f"Script failed in final block: {str(e)}"
        print(f"DEBUG: {error_info}", flush=True)
        logger.error(error_info)
        job.meta['progress'] = error_info
        job.set_status('failed')
        job.save_meta()
        return "Script Failed"




# --- OTRAS TAREAS MANTENIDAS INTACTAS ---
@job
def analyze_protein(protein_file):
    return "A,B"

@job
def analyze_ligand(ligand_file):
    return "A,B"

@job
def process_pockets(protein_file, chains):
    logger = logging.getLogger(__name__)
    logger.info("INFO: process_pockets task started")
    
    # 1. Definir rutas seguras (Fallback)
    home_dir = os.environ.get('HOMEDIR') or os.path.expanduser("~")
    script_dir = os.environ.get('SCRIPTDIR') or f"{home_dir}/.local/src/jimag-scripts"

    # 2. Configurar binarios y scripts usando las rutas seguras
    chimera_bin = "/.local/src/chimera/bin/chimera"
    prank_bin = "/.local/src/p2rank_2.4/prank"
    receptor_script = f"{script_dir}/receptor.py"
    prank_conf = f"{script_dir}/configs/blind.groovy"

    try:
        # Preparar archivo de entrada
        with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as inputpdb:
            inputpdb.write(protein_file.read())
            inputpdb.flush()
        
        # Archivo para la proteína limpia (solo cadenas seleccionadas)
        chainspdb = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
        chainspdb.close() # Lo cerramos para que los procesos externos puedan escribir

        # --- PASO 1: CHIMERA (Limpieza de cadenas) ---
        # Preparamos el entorno para el subproceso
        env = os.environ.copy()
        env.update({
            "IF": inputpdb.name,
            "OF": chainspdb.name,
            "CHAINS": chains
        })

        clean_chains_cmd = [chimera_bin, "--nogui", receptor_script]
        logger.info(f"Ejecutando Chimera en {inputpdb.name} para cadenas {chains}")
        subprocess.run(clean_chains_cmd, env=env, check=True)
        
        # --- PASO 2: P2RANK (Predicción de bolsillos) ---
        pockets_cmd = [
            prank_bin, "predict", 
            "-c", prank_conf, 
            "-f", chainspdb.name, 
            "-o", "/tmp/"
        ]
        logger.info(f"Ejecutando P2Rank sobre {chainspdb.name}")
        subprocess.run(pockets_cmd, check=True)
        
        # Rutas de salida
        pockets_csv = f'{chainspdb.name}_predictions.csv'
        clean_protein_path = chainspdb.name

        # Limpieza de archivo temporal inicial
        if os.path.exists(inputpdb.name):
            os.remove(inputpdb.name)
        
        return pockets_csv, clean_protein_path

    except subprocess.CalledProcessError as e:
        error_msg = f"Error en ejecución de comando externo: {e}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"Error general en process_pockets: {str(e)}"
        logger.error(error_msg)
        return error_msg