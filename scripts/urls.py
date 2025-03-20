from django.urls import path
from . import views  # Importa las vistas desde el mismo directorio

urlpatterns = [
    path('', views.index, name='index'),
    path('install/', views.install_7zip, name='install_7zip'),
    path('uninstall/', views.uninstall_7zip, name='uninstall_7zip'),
    path('shutdown/', views.shutdown_pc01, name='shutdown_pc01'),
    path('monitor/', views.monitor, name='monitor'),
    path('software/', views.software, name='software'),
    path('control/', views.control, name='control'),
]