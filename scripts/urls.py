from django.urls import path
from scripts import views

urlpatterns = [
    path('', views.index, name='index'),
    path('install_7zip/', views.install_7zip, name='install_7zip'),
    path('uninstall_7zip/', views.uninstall_7zip, name='uninstall_7zip'),
    path('shutdown_pc01/', views.shutdown_pc01, name='shutdown_pc01'),
    path('restart_pc01/', views.restart_pc01, name='restart_pc01'),
    path('remote_desktop_pc01/', views.remote_desktop_pc01, name='remote_desktop_pc01'),
    path('monitor/', views.monitor, name='monitor'),
    path('software/', views.software, name='software'),
    path('control/', views.control, name='control'),
]