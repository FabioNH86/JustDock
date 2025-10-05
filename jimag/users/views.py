from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.db import IntegrityError


# Create your views here.
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html', {
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = User.objects.create_user(username=request.POST['username'], password=request.POST['password1'])
                # send the user to the database
                user.save()
                login(request, user)
                return redirect('jobs')
            except IntegrityError:
                return render(request, 'register.html', {
                    'form': UserCreationForm,
                    'error': 'Username already exists!'
                })
        return render(request, 'register.html', {
            'form': UserCreationForm,
            'error': 'Passwords do not match!'
        })


def log_out(request):
    logout(request)
    return redirect('home')


def log_in(request):
    if request.method == 'GET':
        return render(request, 'login.html', {
            'form': AuthenticationForm
        })
    else:
        user = authenticate(
            request, username=request.POST['username'], password=request.POST
            ['password'])
        if user is None:
            return render(request, 'login.html', {
                'form': AuthenticationForm,
                'error': 'Username or password is incorrect'
            })
        else:
            login(request, user)
            return redirect('jobs')
