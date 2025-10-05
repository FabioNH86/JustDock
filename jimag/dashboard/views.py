import os
from django.shortcuts import render, redirect
from jobs.models import Job, Docking, Protein, Ligand
from django.http import FileResponse, HttpResponse, HttpResponseForbidden
from django.http import HttpResponse
from django.conf import settings
import shutil
import zipfile
import json


# Create your views here.
def results(request, current_job=None, current_docking=None, current_pocket=None):
    #everything is done on basis of the current user
    user = request.user
    jobs = Job.objects.filter(user=user)

    #current_job starts with a non-null value if the user directly visits the job id via url
    if not current_job:
        latest_job = user.profile.latest_job
        if not latest_job: #if latest_job is null
            # todo: consider the case where the user has no jobs
            # TODO: This is redundant with the lines in delete_job()
            job_ids = jobs.values_list('id', flat=True)
            first_job = min(job_ids)
            current_job = first_job
        else:
            current_job = latest_job
    if Job.objects.get(pk=current_job).user != request.user:
        return HttpResponseForbidden("You don't have access to this job.")

    dockings = Docking.objects.filter(job=current_job)
    if current_docking == None or current_docking == 0:
        #find the first docking IN THE CURRENT JOB 
        #TODO: cache this value so that it doesn't get calculated every time we change pockets in the same docking
        docking_ids = dockings.values_list('id', flat=True)
        first_docking = min(docking_ids)
        current_docking = first_docking
        #current_docking = Docking.objects.get(job=current_job).id
    docking = current_docking
    print("DOCKING: ", current_docking)

    if not current_pocket:
        current_pocket = [int(pocket) for pocket in Docking.objects.get(pk=docking).pockets.split(',')][0]

    wd = f"user_{user.id}/job_{current_job}/"
    cpd = f"{wd}docking_{docking}/pocket_{current_pocket}/" # current pocket directory

    current_job_files = {
        'conformers': f"/media/{cpd}modes.pdbqt",
        'receptor': f"/media/{wd}receptor.pdbqt",
    }
    vina_file = f"{settings.MEDIA_ROOT}/{cpd}scores.txt"
    with open(vina_file, 'r') as file:
        vina_results = file.read()

    print("DOCKINGS: ", dockings)
    return render(request, 'dashboard.html', {
        'job_info': job_info(current_job),
        'current_job': current_job,
        'current_job_files': current_job_files,
        'current_docking' : current_docking,
        'current_pocket': current_pocket,
        'vina_results': vina_results,
        #'jobs': [job for job in Job.objects.filter(user=user)],
        'jobs': list(jobs.order_by('-id')),
        'dockings': list(Docking.objects.filter(job=current_job)),
        'pockets': [int(pocket) for pocket in dockings.get(pk=docking).pockets.split(',')]  # current job pockets
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
