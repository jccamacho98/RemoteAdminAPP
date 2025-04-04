from django.urls import path
from . import views

urlpatterns = [
    path('', views.control, name='control'),
    path('action/shutdown/', views.control, name='shutdown_pc01'),
    path('action/restart/', views.control, name='restart_pc01'),
    path('action/remote_desktop/', views.control, name='remote_desktop_pc01'),
]