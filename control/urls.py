from django.urls import path
from . import views

urlpatterns = [
    path('', views.control, name='control'),
    path('get_task_status/', views.get_task_status, name='get_task_status'),
    path('clear_rdp_session/', views.control, name='clear_rdp_session'),
]