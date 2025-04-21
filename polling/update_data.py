import os
from django.utils import timezone
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script
from django.conf import settings

def update_dynamic_data():
    # Usar settings.BASE_DIR para obtener el directorio raíz del proyecto (C:\WebAdminDev)
    project_root = settings.BASE_DIR
    # Construir la ruta a ScriptsPS/CheckStatus.ps1
    script_path = os.path.join(project_root, 'ScriptsPS', 'CheckStatus.ps1')
    
    for pc in Info_PCs.objects.all():
        output = run_powershell_script(script_path, args=f'"{pc.nombre}"')
        if output.startswith("Error"):
            print(f"Error al actualizar {pc.nombre}: {output}")
            pc.estado = "Offline"
            pc.last_seen = timezone.now()
            pc.save()
            continue
        
        try:
            # Parsear la salida del script
            status = "Offline"
            for line in output.splitlines():
                if line.startswith("Status:"):
                    status = line.split("Status: ")[1].strip()
                    break
                else:
                    print(f"Salida de {pc.nombre}: {line}")
            
            # Actualizar el registro
            pc.estado = status
            pc.last_seen = timezone.now()
            pc.save()
            print(f"Actualizado {pc.nombre}: Estado={pc.estado}")
        except Exception as e:
            print(f"Error al procesar la salida para {pc.nombre}: {str(e)}")
            pc.estado = "Offline"
            pc.last_seen = timezone.now()
            pc.save()