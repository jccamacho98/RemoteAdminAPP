import time
from django.core.management.base import BaseCommand
from polling.update_data import update_dynamic_data

class Command(BaseCommand):
    help = 'Actualiza los datos dinámicos de los PCs cada 2 minutos'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando actualización dinámica de datos...'))
        
        while True:
            try:
                # Ejecutar la función de actualización
                update_dynamic_data()
                self.stdout.write(self.style.SUCCESS('Datos actualizados. Esperando 2 minutos para la próxima actualización...'))
                
                # Esperar 2 minutos (120 segundos)
                time.sleep(120)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error durante la actualización: {str(e)}'))
                # Esperar 2 minutos antes de intentar de nuevo
                time.sleep(120)