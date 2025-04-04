import time
from django.core.management.base import BaseCommand
from scripts.utils import update_pc_info

class Command(BaseCommand):
    help = 'Actualiza la información detallada de los PCs una vez al día'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando actualización diaria de información detallada...'))
        
        while True:
            try:
                result = update_pc_info()
                self.stdout.write(self.style.SUCCESS('Información detallada actualizada:'))
                self.stdout.write(result)
                self.stdout.write(self.style.SUCCESS('Esperando 24 horas para la próxima actualización...'))
                time.sleep(86400)  # 24 horas (24 * 60 * 60 segundos)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error durante la actualización: {str(e)}'))
                time.sleep(86400)