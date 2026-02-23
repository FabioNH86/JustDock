import os
from django.shortcuts import render, redirect
from jobs.models import Job, Docking, Protein, Ligand
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.http import HttpResponse
from django.conf import settings
import shutil
import zipfile
import json
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)

# Create your views here.
def results(request, current_job=None, current_docking=None, current_pocket=None):
    user = request.user
    # Ordenamos por ID descendente para ver lo más reciente primero
    jobs = Job.objects.filter(user=user).order_by('-id')

    if not jobs.exists():
        return render(request, 'dashboard.html', {'error': 'No tienes trabajos creados.'})

    # Determinar el Job actual
    if not current_job:
        latest_job_id = user.profile.latest_job
        if latest_job_id and jobs.filter(pk=latest_job_id).exists():
            current_job = latest_job_id
        else:
            current_job = jobs.first().id

    # Verificación de seguridad y obtención de instancia
    try:
        job_instance = Job.objects.get(pk=current_job)
    except Job.DoesNotExist:
        return redirect('results') # O manejar el error

    if job_instance.user != user:
        return HttpResponseForbidden("No tienes acceso a este trabajo.")

    # Obtener dockings asociados
    dockings = Docking.objects.filter(job=job_instance)

    # Manejo de caso sin resultados aún
    if not dockings.exists():
        return render(request, 'dashboard.html', {
            'job_info': job_info(current_job) if job_instance.status == 'finished' else None,
            'current_job': current_job,
            'jobs': list(jobs),
            'no_dockings': True,
            'status': job_instance.status
        })
    
    # Determinar Docking actual
    if current_docking == None or current_docking == 0:
        current_docking = dockings.first().id
            
    docking_instance = Docking.objects.get(pk=current_docking)

    # Determinar Pocket actual
    if not current_pocket:
        try:
            # Separamos el string de pockets (ej: "1,2,3") y tomamos el primero
            current_pocket = [int(p) for p in docking_instance.pockets.split(',')][0]
        except (ValueError, IndexError, AttributeError):
            current_pocket = 1

    # --- CORRECCIÓN DE RUTAS ---
    wd = f"user_{user.id}/job_{current_job}/"
    # Cambiado 'docking' por 'current_docking'
    cpd = f"{wd}docking_{current_docking}/pocket_{current_pocket}/" 

    current_job_files = {
        'conformers': f"/media/{cpd}modes.pdbqt",
        'receptor': f"/media/{wd}receptor.pdbqt",
    }
    
    vina_file = os.path.join(settings.MEDIA_ROOT, cpd, "scores.txt")
    
    try:
        with open(vina_file, 'r') as file:
            vina_results = file.read()
    except (FileNotFoundError, OSError):
        vina_results = None

    # Preparar lista de pockets para el selector del template
    try:
        pocket_list = [int(p) for p in docking_instance.pockets.split(',')]
    except:
        pocket_list = [current_pocket]

    return render(request, 'dashboard.html', {
        'job_info': job_info(current_job),
        'current_job': current_job,
        'current_job_files': current_job_files,
        'current_docking' : current_docking,
        'current_pocket': current_pocket,
        'vina_results': vina_results,
        'jobs': list(jobs),
        'dockings': list(dockings),
        'pockets': pocket_list 
    })


def download_output(request, current_job):
    user = request.user
    td = f"{settings.MEDIA_ROOT}/user_{user.id}/tmp/"
    wd = f"{settings.MEDIA_ROOT}/user_{user.id}/job_{current_job}/"

    os.makedirs(td, exist_ok=True)

    print(f"zipping {wd}")
    shutil.make_archive(f"{td}output", 'zip', wd, verbose=True)
    # create response to send the ZIP file for download
    response = FileResponse(open(f"{td}output.zip", 'rb'), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="output.zip"'
    return response


def job_info(job_id):
    job_instance = Job.objects.get(pk=job_id)
    info = {}
    info['type'] = job_instance.job_type
    info['created_at'] = job_instance.created_at
    info['receptor'] = Protein.objects.get(job=job_id).protein_name
    info['ligand'] = Ligand.objects.get(job=job_id).ligand_name
    #this needs refactoring becuase jobs can now have multiple dockings
    info['pockets'] = Docking.objects.filter(job=job_id).first().pockets
    return info


def delete_job(request, job_id):
    user = request.user
    job_instance = Job.objects.get(pk=job_id)
    job_dir = f"{settings.MEDIA_ROOT}/user_{user.id}/job_{job_id}"
    # TODO: remove redundant code
    if request.method == 'POST':
        if job_id == user.profile.latest_job:
            try:
                shutil.rmtree(job_dir)
            except OSError as e:
                print(f"Error deleting directory: {e}")

            job_instance.delete()
            user.profile.latest_job = None
            user.profile.save()
            # user.profile.latest_job.delete()
            user_job_ids = Job.objects.filter(user=user).values_list('id', flat=True)
            first_job = min(user_job_ids)
            return redirect('results', current_job=first_job)
        else:
            try:
                shutil.rmtree(job_dir)
            except OSError as e:
                print(f"Error deleting directory: {e}")

            job_instance.delete()
            return redirect('results')
