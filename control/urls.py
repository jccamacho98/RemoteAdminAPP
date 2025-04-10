from django.urls import path
from . import views

urlpatterns = [
    path('', views.control, name='control'),
    path('action/shutdown/', views.control, name='shutdown'),
    path('action/restart/', views.control, name='restart'),
    path('action/remote_desktop/', views.control, name='remote_desktop'),
    path('download_rdp/<str:pc_name>/', views.download_rdp, name='download_rdp'),
    path('get_task_status/', views.get_task_status, name='get_task_status'),
]