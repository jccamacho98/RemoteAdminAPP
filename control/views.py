from django.shortcuts import render
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
from django.utils import timezone
import os
import uuid
from django.conf import settings
from django.http import FileResponse

def control(request):
    # Obtener solo los PCs que están Online
    online_pcs = Info_PCs.objects.filter(estado="Online").order_by('nombre')
    output = None

    # Listar los archivos disponibles en la carpeta SharedFiles
    shared_files_dir = os.path.join(settings.BASE_DIR, 'SharedFiles')
    available_files = []
    if os.path.exists(shared_files_dir):
        available_files = [f for f in os.listdir(shared_files_dir) if os.path.isfile(os.path.join(shared_files_dir, f))]
    else:
        available_files = []
        output = "Advertencia: La carpeta SharedFiles no existe en el servidor."

    # Manejar la acción de copiar archivo (POST)
    if request.method == "POST" and 'copy_file' in request.POST:
        print("Entrando en copy_file")  # Depuración
        selected_pcs = request.POST.getlist('selected_pcs')
        print(f"Selected PCs: {selected_pcs}")  # Depuración
        if not selected_pcs:
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            '   output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
        })
        # Determinar la fuente del archivo (subir o seleccionar del servidor)
        file_source = request.POST.get('file_source')
        source_file_path = None
        file_to_copy = None

        if file_source == "upload":
            if 'file_to_upload' not in request.FILES:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione un archivo para subir."
                })

            file_to_copy = request.FILES['file_to_upload']
            
            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if file_to_copy.size > max_file_size:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."
                })

            temp_filename = f"{uuid.uuid4()}_{file_to_copy.name}"
            temp_file_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'temp', temp_filename)
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            try:
                with open(temp_file_path, 'wb') as f:
                    for chunk in file_to_copy.chunks():
                        f.write(chunk)
            except Exception as e:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error al guardar el archivo temporal: {str(e)}"
                })

            if not os.path.exists(temp_file_path):
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: No se pudo crear el archivo temporal en {temp_file_path}."
                })

            if os.path.getsize(temp_file_path) == 0:
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo temporal {temp_file_path} está vacío."
                })

            source_file_path = temp_file_path
            file_to_copy_name = file_to_copy.name

        elif file_source == "server":
            if 'file_from_server' not in request.POST or not request.POST['file_from_server']:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione un archivo del servidor."
                })

            file_to_copy_name = request.POST['file_from_server']
            source_file_path = os.path.join(shared_files_dir, file_to_copy_name)

            if not os.path.exists(source_file_path):
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo {file_to_copy_name} no existe en el servidor."
                })

            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if os.path.getsize(source_file_path) > max_file_size:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."
                })

            if os.path.getsize(source_file_path) == 0:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo {file_to_copy_name} está vacío."
                })

        else:
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
                'output': "Error: Opción de fuente de archivo no válida."
            })

        remote_destination = f"C:\\Archivos compartidos Server\\{file_to_copy_name}"
        script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'CopyFileToPC.ps1')
        output = []
        for pc_name in selected_pcs:
            try:
                pc = Info_PCs.objects.get(nombre=pc_name)
                if pc.estado != "Online":
                    output.append(f"Error: El PC {pc_name} está offline y no se puede copiar el archivo.")
                    continue
            except Info_PCs.DoesNotExist:
                output.append(f"Error: El PC {pc_name} no existe en la base de datos.")
                continue

            source_file_path = source_file_path.replace('/', '\\')
            remote_destination = remote_destination.replace('/', '\\')
            args = f'"{pc_name}" "{source_file_path}" "{remote_destination}"'
            result = run_powershell_script(script_path, args=args)
            output.append(f"Resultado para {pc_name}:\n{result}\n")

        if file_source == "upload":
            try:
                os.remove(source_file_path)
            except Exception as e:
                output.append(f"Advertencia: No se pudo eliminar el archivo temporal {source_file_path}: {str(e)}\n")

        output = "\n".join(output)

    # Manejar las acciones de apagar, reiniciar y escritorio remoto (GET)
    if request.method == "GET":
        selected_pcs = request.GET.getlist('selected_pcs')
        if not selected_pcs:
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
                'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
            })

        if request.path.endswith('action/shutdown/'):
            output = []
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ApagarPC.ps1')
            for pc_name in selected_pcs:
                result = run_powershell_script(script_path, args=f'"{pc_name}"')
                output.append(f"Resultado para {pc_name}:\n{result}\n")
                pc = Info_PCs.objects.get(nombre=pc_name)
                pc.estado = "Offline" if "Éxito" in result else "Offline"
                pc.last_seen = timezone.now()
                pc.save()
            output = "\n".join(output)

        elif request.path.endswith('action/restart/'):
            output = []
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ReiniciarPC.ps1')
            for pc_name in selected_pcs:
                result = run_powershell_script(script_path, args=f'"{pc_name}"')
                output.append(f"Resultado para {pc_name}:\n{result}\n")
                pc = Info_PCs.objects.get(nombre=pc_name)
                pc.estado = "Online" if "Éxito" in result else "Offline"
                pc.last_seen = timezone.now()
                pc.save()
            output = "\n".join(output)

        elif request.path.endswith('action/remote_desktop/'):
            if len(selected_pcs) > 1:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC."
                })
            
            pc_name = selected_pcs[0]
            rdp_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', f'{pc_name}.rdp')
            if os.path.exists(rdp_path):
                pc = Info_PCs.objects.get(nombre=pc_name)
                pc.last_seen = timezone.now()
                pc.save()
                return FileResponse(
                    open(rdp_path, 'rb'),
                    as_attachment=True,
                    filename=f'{pc_name}.rdp'
                )
            else:
                output = f"Error: El archivo {pc_name}.rdp no existe en {os.path.join(settings.BASE_DIR, 'ScriptsPS')}."

    return render(request, 'control/control.html', {
        'online_pcs': online_pcs,
        'available_files': available_files,
        'output': output
    })