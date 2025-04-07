from django.urls import path
from . import views

urlpatterns = [
    path('', views.control, name='control'),
    path('action/shutdown/', views.control, name='shutdown'),
    path('action/restart/', views.control, name='restart'),
    path('action/remote_desktop/', views.control, name='remote_desktop'),
]