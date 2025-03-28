from django.urls import path
from . import views

urlpatterns = [
    path('', views.control, name='control'),
    path('shutdown_pc01/', views.shutdown_pc01, name='shutdown_pc01'),
    path('restart_pc01/', views.restart_pc01, name='restart_pc01'),
    path('remote_desktop_pc01/', views.remote_desktop_pc01, name='remote_desktop_pc01'),
]