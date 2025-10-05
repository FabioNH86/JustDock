"""
URL configuration for jimag project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core.views import home, about
from jobs.views import jobs, rundocking, check_progress, \
    process_protein, process_ligand, load_pockets, retrieve_pockets, dummy
from users.views import register, log_in, log_out
from dashboard.views import results, delete_job, download_output

urlpatterns = [
    path('admin/', admin.site.urls),
    # path('', views.main),
    path('home/', home, name='home'),
    path('about/', about, name='about'),
    path('register/', register, name='register'),
    path('jobs/', jobs, name='jobs'),
    path('process_protein/', process_protein, name='process_protein'),
    path('load_pockets/', load_pockets, name='load_pockets'),
    path('retrieve_pockets/<str:job_id>/', retrieve_pockets, name='retrieve_pockets'),
    path('process_ligand/', process_ligand, name='process_ligand'),
    path('logout/', log_out, name='logout'),
    path('login/', log_in, name='login'),
    path('run-docking/', rundocking, name='run_docking'),
    path('check_progress/', check_progress, name='check_progress'),
    path('results/', results, name='results'),
    path('results/<int:current_job>/<int:current_docking>/<int:current_pocket>', results, name='results'),
    path('delete-job/<int:job_id>', delete_job, name='delete_job'),
    path('download_output/<int:current_job>', download_output, name='download_output'),
    path('dummy/', dummy, name='dummy'),
    # TODO: delete this
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
