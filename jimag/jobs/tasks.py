from rq import get_current_job
from django_rq import job
from .models import Docking, Protein, Ligand, User, Job
import subprocess
import logging
import tempfile
import shutil
import os

logging.basicConfig(filename='script_output.log', level=logging.DEBUG)


@job
def run_docking_script(user_id, job_id, settings):
    job = get_current_job()  # is this line necessary?

    
    logger = logging.getLogger(__name__)
    logger.info("INFO: run_docking_script task started")

    #pre-docking process
    try:
        script_path = f"{os.environ.get('SCRIPTDIR')}/multi.sh"
        working_dir = f"{os.environ.get('PROJECTROOT')}/media/user_{user_id}/job_{job_id}"
        input_dir = f"{working_dir}/input"

        # Pass preprocessing files to the script, add flags as necessary
        if settings['preproc_done']:
            os.makedirs(working_dir, exist_ok=True)
            shutil.copy(settings['pockets_filename'], f"{working_dir}/receptor.pdb_predictions.csv")
            shutil.copy(settings['clean_protein_filename'], f"{working_dir}/receptor.pdb")

        script_command = [script_path, "--input", input_dir, "--wd", working_dir,
                          "--vinalvl", settings['exhaustiveness'], "--num_modes",
                          settings['num_modes'], "--run_mode", "predock"]
        if settings['chains']:
            script_command.extend(["--chains", settings['chains']])
        if settings['pockets']:
            script_command.extend([settings['pockets']['option'], settings['pockets']['value']])
        if settings['preproc_done'] is True:
            script_command.extend(["--preproc_done"])

        # running and logging (helper function)
        def run_script(cmd):
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            output_lines = []
            for line in process.stdout:
                line = line.strip()
                output_lines.append(line)
                job.meta['progress'] = '\n'.join(output_lines)
                job.save_meta()
                logger.info(line)

            return_code = process.wait()

            if return_code != 0:
                logger.error(f"Script failed with code {return_code}")
                job.meta['progress'] = f"Script failed with code {return_code}"
                job.set_status('failed')
                job.save_meta()
                return False

            return True

        if not run_script(script_command):
            return "Preprocessing failed"

        #read generated pockets info
        pockets_file = open(f"{working_dir}/pockets", 'r')
        pocket_str = pockets_file.readline()  # pockets are saved in a single line in this file
        pockets_file.close()

        #helper function to edit (change/add) command flags 
        def update_setting(cmd, flag, value):
            if flag in cmd:
                index = cmd.index(flag)
                cmd[index+1] = value
            else:
                cmd.extend([flag,value])

        #the actual docking(s)
        script_command.extend(["--output", ""])
        for run in range(1, int(settings['num_runs']) + 1):
            p, l = Protein.objects.get(job=job_id), Ligand.objects.get(job=job_id)
            docking = Docking.objects.create(
                user=User.objects.get(id=user_id),
                job=Job.objects.get(id=job_id),
                protein=p,
                ligand=l,
                pockets=pocket_str
            )
            p.docking, l.docking = docking.id, docking.id
            p.save()
            l.save()

            output_dir = f"{working_dir}/docking_{docking.id}"
            update_setting(script_command, "--run_mode", "dock_only")
            update_setting(script_command, "--output", output_dir)
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f'CURRENT COMMAND: {script_command}')

            if not run_script(script_command):
                return "Preprocessing failed"

    except Exception as e:
        logger.error(f"Script failed: {str(e)}")
        job.meta['progress'] = f"Script failed: {str(e)}"
        job.set_status('failed')

    logger.info("Script completed successfully")

    job.meta['progress'] = "Script completed successfully"
    job.set_status('completed')
    job.save_meta()

    return "Script completed successfully"


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

    try:
        # prepare protein file as tempfile for shell handling
        with tempfile.NamedTemporaryFile(suffix=".pdb", delete=False) as inputpdb:
            inputpdb.write(protein_file.read())
            inputpdb.flush()
        # clean chains
        script_path = f"{os.environ.get('SCRIPTDIR')}/receptor.py"
        chimera_cmd = f"{os.environ.get('HOMEDIR')}/.local/src/chimera/bin/chimera"
        chainspdb = tempfile.NamedTemporaryFile(suffix=".pdb", delete=False)
        clean_chains_cmd = f'export IF={inputpdb.name} OF={chainspdb.name} CHAINS={chains}; {chimera_cmd} --nogui {script_path}'
        subprocess.run(clean_chains_cmd, shell=True)
        # chainspdb.flush()
        # get pockets with p2rank
        prankcmd = f"{os.environ.get('HOMEDIR')}/.local/src/p2rank_2.4/prank"
        prankconf = f"{os.environ.get('SCRIPTDIR')}/configs/blind.groovy"
        # pockets = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        # pockets_cmd = f'{prankcmd} predict -c {prankconf} -f {chainspdb.name} -o {pockets.name}'
        pockets_cmd = f'{prankcmd} predict -c {prankconf} -f {chainspdb.name} -o /tmp/'
        subprocess.run(pockets_cmd, shell=True)
        # pockets.flush()
        pockets = f'{chainspdb.name}_predictions.csv'
        clean_protein = chainspdb.name
        # TODO: explicitly delete the tempfiles without affecting their collection for docking

        inputpdb.close()
        chainspdb.close()
        # return pockets.name
        return pockets, clean_protein
    except Exception as e:
        return f"{str(e)}"
