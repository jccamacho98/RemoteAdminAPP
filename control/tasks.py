from celery import shared_task
from scripts.utils import run_powershell_script
from monitor.models import Info_PCs
from django.contrib import messages

@shared_task
def copy_file_to_pcs(selected_pcs, source_file_path, file_to_copy_name, script_path):
    results = []
    remote_destination = f"C:\\Archivos compartidos Server\\{file_to_copy_name}"

    for pc_name in selected_pcs:
        try:
            pc = Info_PCs.objects.get(nombre=pc_name)
            if pc.estado != "Online":
                results.append(f"Error: El PC {pc_name} está offline y no se puede copiar el archivo.")
                continue
        except Info_PCs.DoesNotExist:
            results.append(f"Error: El PC {pc_name} no existe en la base de datos.")
            continue

        source_file_path = source_file_path.replace('/', '\\')
        remote_destination = remote_destination.replace('/', '\\')
        args = f'"{pc_name}" "{source_file_path}" "{remote_destination}"'
        result = run_powershell_script(script_path, args=args)
        results.append(f"Resultado para {pc_name}:\n{result}")

    return results