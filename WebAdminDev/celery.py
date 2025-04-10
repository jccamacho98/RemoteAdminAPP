import os
from celery import Celery

# Establece el módulo de configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebAdminDev.settings')

# Crea una instancia de Celery
app = Celery('WebAdminDev')

# Carga la configuración de Celery desde las settings de Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Descubre tareas automáticamente en las aplicaciones de Django
app.autodiscover_tasks()