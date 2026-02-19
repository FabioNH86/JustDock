from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import Job, Docking, Profile
from rq.job import Job as rqJob
from django_rq import get_queue
from .tasks import run_docking_script, analyze_protein, analyze_ligand, process_pockets
from django.urls import reverse
import os
import json
import subprocess

from .forms import ProteinForm, LigandForm, DockingForm


# Create your views here.
def process_protein(request):
    # currently the processing is being handled by the store functions
    if request.method == "POST" and 'protein_file' in request.FILES:
        # TODO: we should get rid of the first check in
        # store_protein and store_ligand
        # checks and extra functionality
        protein_file = request.FILES['protein_file']
        analyze_protein.delay(protein_file)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse(
                {'status': 'success',
                 'protein_file': protein_file.read().decode()})
        else:
            return render(request, 'jobs.html')  # process the job


def process_ligand(request):
    if request.method == "POST":
        if 'ligand_file' in request.FILES:
            ligand_file = request.FILES['ligand_file']
            analyze_ligand.delay(ligand_file)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse(
                    {'status': 'success',
                     'ligand_file': ligand_file.read().decode()})
            else:
                return render(request, 'jobs.html')  # process the job
    elif request.method == "GET":
        ligand_form = LigandForm()
        return render(request, 'jobs.html')


def load_pockets(request):
    chains = request.POST.get('chainString')
    protein_file = request.FILES['protein_file']
    pockets_job = process_pockets.delay(protein_file, chains)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'job_id': pockets_job.id})


def retrieve_pockets(request, job_id):
    queue = get_queue('default')
    # job_id = request.GET.get("job_id")
    job = rqJob.fetch(job_id, connection=queue.connection)

    if job:
        if job.is_finished:
            pockets_filename, clean_protein_filename = job.result
            with open(pockets_filename, "r") as file:
                pockets_file_content = file.read()
            return JsonResponse({'pockets_file_content': pockets_file_content,
                                 'pockets_filename': pockets_filename,
                                 'clean_protein_filename': clean_protein_filename})
        else:
            return JsonResponse({'status': 'pending'})
    else: 
        return JsonResponse({'error': 'Invalid job ID'})


def jobs(request):
    if request.method == 'POST':  # prepare the model instances and run job
        post_type = request.POST.get('type')
        if post_type == 'process_protein':
            process_protein(request)
        elif post_type == 'process_ligand':
            print('process_ligand')
        # elif post_type == 'load_pockets':
        #    print('load_pockets')

        # elif post_type == 'run_job':
        elif post_type == 'run_job':
            settings = {'exhaustiveness': request.POST.get('exhaustiveness'),
                        'num_modes': request.POST.get('modes'),
                        'num_runs': request.POST.get('runs'),
                        'chains': request.POST.get('chainString'),
                        'pockets': json.loads(request.POST.get('pockets')),
                        'preproc_done': request.POST.get('preprocDone')}
            if settings['preproc_done']:
                settings.update({'pockets_filename': request.POST.get('pocketsFilename'),
                                 'clean_protein_filename': request.POST.get('cleanProteinFilename')})
            docking_form = DockingForm(request.POST, request.FILES)
            #THIS IS IMPORTANT. DOES HAVING TWO IDENTICAL CSRF TOKENS PROVOKE THE DOUBLE SUBMISSION?
            print("POST: ", request.POST)

            job = init_job(request)
            store_protein(request, job)
            store_ligand(request, job)
            request.meta_data = {
                'processed': True
            }
            request.session['job_metadata'] = [request.user.id,
                                               job.id, settings]
            return redirect(reverse('run_docking'))                  # RUN!
    else:
        # render the jobs application
        if request.user.is_authenticated:
            docking_form = DockingForm()
            return render(request, 'jobs.html', {
                'docking_form': docking_form
            })
        else:
            return redirect('login')


def init_job(request):
    # Create and link a new Job instance
    job = Job.objects.create(
        job_type='docking',
        user=request.user,
    )
    job.job_name = f"job_{job.id}"
    job.save()

    """
    docking = Docking.objects.create(
        user=request.user,
        job=job,
    )
    """
    return job


def store_protein(request, job):
    # if 'protein_file' in request.FILES:  # will this still be necessary?
    protein_file = request.FILES['protein_file']
    protein_form = ProteinForm(request.POST, request.FILES)
    if protein_form.is_valid():
        protein = protein_form.save(commit=False)
        protein.user = request.user
        protein.job = job
        file_ext = os.path.splitext(protein.protein_file.name)[1]
        protein.protein_file.name = f'receptor{file_ext}'
        protein.save()


def store_ligand(request, job):
    if 'ligand_file' in request.FILES:
        ligand_form = LigandForm(request.POST, request.FILES)
        if ligand_form.is_valid():
            ligand = ligand_form.save(commit=False)
            ligand.user = request.user
            ligand.job = job
            file_ext = os.path.splitext(ligand.ligand_file.name)[1]
            ligand.ligand_file.name = f'ligand{file_ext}'
            ligand.save()


def rundocking(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return HttpResponse(status=204)
    else:
        user, job, settings = request.session.get('job_metadata', [])
        result = run_docking_script.delay(user, job, settings)
        job_id = result.id
        return render(request, 'running.html', {'job_id': job_id})


def check_progress(request):
    queue = get_queue('default')
    job_id = request.GET.get("job_id")
    job = rqJob.fetch(job_id, connection=queue.connection)

    # job.meta gets the status update from rundocking (including script logs)
    progress = job.meta.get('progress', 'Running')

    if progress == "Script completed successfully":
        user_inst, job_inst, settings = request.session.get('job_metadata')

        if hasattr(request.user, 'profile'):
            request.user.profile.latest_job = job_inst
            request.user.profile.save()
        else:
            profile = Profile.objects.create(
                user=request.user,
                latest_job=job_inst,
            )
            profile.save()

        redirect_url = reverse('results')
        return JsonResponse({'progress': progress,
                             'redirect_url': redirect_url})

    # output = job.meta.get('output', [])
    # current_output = '\n'.join(output)
    # TODO: see if we can log the progress incrementally (not sending the same past stuff over and over)
    # print("PROGRESS LOG: ", progress)
    # output lets us directly log the script output to the django console
    # return JsonResponse({'progress': progress, 'output': output})
    return JsonResponse({'progress': progress})


def dummy(request):
    return render(request, 'dummy.html')
