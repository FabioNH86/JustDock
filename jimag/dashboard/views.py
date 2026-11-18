import os
from django.shortcuts import render, redirect
from jobs.models import Job, Docking, Protein, Ligand, Profile
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.http import HttpResponse
from django.conf import settings
import shutil
import zipfile
import json


# Create your views here.
def results(request, current_job=None, current_docking=None, current_pocket=None):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)
    jobs = Job.objects.filter(user=user).order_by('-id')

    # Empty-state: user has no jobs at all
    if not jobs.exists():
        return render(request, 'dashboard.html', {'error': 'No tienes trabajos creados.'})

    # Determine current job
    if not current_job:
        latest_job_id = profile.latest_job
        if latest_job_id and jobs.filter(pk=latest_job_id).exists():
            current_job = latest_job_id
        else:
            current_job = jobs.first().id

    # Security: job must belong to this user
    job_instance = Job.objects.filter(pk=current_job, user=user).first()
    if job_instance is None:
        return HttpResponseForbidden("You don't have access to this job.")

    # Dockings for this job
    dockings = Docking.objects.filter(job=current_job)
    if not dockings.exists():
        return render(request, 'dashboard.html', {
            'job_info': job_info(current_job) if job_instance.status == 'finished' else None,
            'current_job': current_job,
            'jobs': list(jobs),
            'no_dockings': True,
            'status': job_instance.status,
        })

    if current_docking is None or current_docking == 0:
        current_docking = dockings.first().id

    docking_instance = Docking.objects.get(pk=current_docking)

    if not current_pocket:
        try:
            current_pocket = [int(p) for p in docking_instance.pockets.split(',')][0]
        except (ValueError, IndexError, AttributeError):
            current_pocket = 1

    wd = f"user_{user.id}/job_{current_job}/"
    cpd = f"{wd}docking_{current_docking}/pocket_{current_pocket}/"

    current_job_files = {
        'conformers': f"/media/{cpd}modes.pdbqt",
        'receptor': f"/media/{wd}receptor.pdbqt",
    }

    vina_file = f"{settings.MEDIA_ROOT}/{cpd}scores.txt"
    try:
        with open(vina_file, 'r') as file:
            vina_results = file.read()
    except FileNotFoundError:
        vina_results = ''

    return render(request, 'dashboard.html', {
        'job_info': job_info(current_job),
        'current_job': current_job,
        'current_job_files': current_job_files,
        'current_docking': current_docking,
        'current_pocket': current_pocket,
        'vina_results': vina_results,
        'jobs': list(jobs),
        'dockings': list(dockings),
        'pockets': [int(p) for p in docking_instance.pockets.split(',')],
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
    first_docking = Docking.objects.filter(job=job_id).first()
    info['pockets'] = first_docking.pockets if first_docking else '' 
    return info


def delete_job(request, job_id):
    user = request.user
    if request.method != 'POST':
        return redirect('results')

    # Solo se pueden borrar jobs propios; si no existe o es de otro usuario, se ignora
    job_instance = Job.objects.filter(pk=job_id, user=user).first()
    if job_instance is None:
        return HttpResponseForbidden("No tienes acceso a este trabajo.")

    job_dir = os.path.join(settings.MEDIA_ROOT, f"user_{user.id}", f"job_{job_id}")
    try:
        shutil.rmtree(job_dir)
    except OSError as e:
        print(f"Error deleting directory: {e}")

    job_instance.delete()

    profile, _ = Profile.objects.get_or_create(user=user)
    if profile.latest_job == job_id:
        # Apuntamos al job más reciente que quede (o None si ya no hay ninguno)
        remaining = Job.objects.filter(user=user).order_by('-id').first()
        profile.latest_job = remaining.id if remaining else None
        profile.save()

    # results() elige el job a mostrar y maneja el caso sin jobs
    return redirect('results')
