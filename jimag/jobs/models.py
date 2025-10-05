# Create your models here.

from django.db import models
from django.contrib.auth.models import User

def gen_filepath(instance, filename):
    user_id = instance.user.id 
    job_id = instance.job.id
    return f"user_{user_id}/job_{job_id}/input/{filename}"

class Job(models.Model):
    job_type = models.CharField(max_length=50)
    job_name = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

class Protein(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    protein_name = models.CharField(max_length=50, default='protein')
    created_at = models.DateTimeField(auto_now_add=True)
    pdb_id = models.CharField(max_length=50)
    protein_file = models.FileField(upload_to=gen_filepath)
    #TODO: how to handle the category? if gen_filepath is not a callable function

class Ligand(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    ligand_name = models.CharField(max_length=50, default='ligand')
    created_at = models.DateTimeField(auto_now_add=True)
    external_id = models.CharField(max_length=50)
    #external_id_type = models.CharField(max_length=50)
    ligand_file = models.FileField(upload_to=gen_filepath)

class Docking(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    protein = models.ForeignKey(Protein, on_delete=models.CASCADE, related_name='dockings')
    ligand = models.ForeignKey(Ligand, on_delete=models.CASCADE, related_name='dockings')
    pockets = models.CharField(max_length=100)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    latest_job = models.PositiveIntegerField(null=True)
