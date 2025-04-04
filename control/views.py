from django.shortcuts import render
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
from django.utils import timezone
import os
import uuid
from django.conf import settings

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
        # Obtener los PCs seleccionados
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
                'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
            })

        # Determinar la fuente del archivo (subir o seleccionar del servidor)
        file_source = request.POST.get('file_source')
        source_file_path = None
        file_to_copy = None

        if file_source == "upload":
            # Opción 1: Subir un archivo desde la máquina local
            if 'file_to_upload' not in request.FILES:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione un archivo para subir."
                })

            file_to_copy = request.FILES['file_to_upload']
            
            # Validar el tamaño del archivo (por ejemplo, máximo 100 MB)
            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if file_to_copy.size > max_file_size:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."
                })

            # Generar un nombre único para el archivo temporal
            temp_filename = f"{uuid.uuid4()}_{file_to_copy.name}"
            temp_file_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'temp', temp_filename)

            # Crear el directorio temporal si no existe
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            # Guardar el archivo temporalmente
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

            # Verificar que el archivo temporal exista
            if not os.path.exists(temp_file_path):
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: No se pudo crear el archivo temporal en {temp_file_path}."
                })

            # Verificar que el archivo temporal tenga datos
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
            # Opción 2: Seleccionar un archivo del servidor
            if 'file_from_server' not in request.POST or not request.POST['file_from_server']:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione un archivo del servidor."
                })

            file_to_copy_name = request.POST['file_from_server']
            source_file_path = os.path.join(shared_files_dir, file_to_copy_name)

            # Validar que el archivo exista en el servidor
            if not os.path.exists(source_file_path):
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo {file_to_copy_name} no existe en el servidor."
                })

            # Validar el tamaño del archivo (por ejemplo, máximo 100 MB)
            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if os.path.getsize(source_file_path) > max_file_size:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."
                })

            # Verificar que el archivo no esté vacío
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

        # Depuración: Imprimir la ruta del archivo
        print(f"Archivo seleccionado: {source_file_path}")

        # Ruta de destino en los PCs remotos
        remote_destination = f"C:\\Archivos compartidos Server\\{file_to_copy_name}"

        # Ejecutar el script para copiar el archivo a cada PC seleccionado
        script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'CopyFileToPC.ps1')
        output = []
        for pc_name in selected_pcs:
            # Validar que el PC siga estando Online
            try:
                pc = Info_PCs.objects.get(nombre=pc_name)
                if pc.estado != "Online":
                    output.append(f"Error: El PC {pc_name} está offline y no se puede copiar el archivo.")
                    continue
            except Info_PCs.DoesNotExist:
                output.append(f"Error: El PC {pc_name} no existe en la base de datos.")
                continue

            # Construir los argumentos para el script
            source_file_path = source_file_path.replace('/', '\\')  # Normalizar la ruta para Windows
            remote_destination = remote_destination.replace('/', '\\')  # Normalizar la ruta para Windows
            args = f'"{pc_name}" "{source_file_path}" "{remote_destination}"'
            # Depuración: Imprimir los argumentos que se pasan al script
            print(f"Ejecutando script para {pc_name} con argumentos: {args}")
            result = run_powershell_script(script_path, args=args)
            output.append(f"Resultado para {pc_name}:\n{result}\n")

        # Eliminar el archivo temporal si se subió uno
        if file_source == "upload":
            try:
                os.remove(source_file_path)
            except Exception as e:
                output.append(f"Advertencia: No se pudo eliminar el archivo temporal {source_file_path}: {str(e)}\n")

        output = "\n".join(output)

    # Resto de las acciones (apagar, reiniciar, escritorio remoto) basadas en la URL (GET)
    if request.method == "GET":
        if request.path.endswith('action/shutdown/'):
            selected_pcs = request.GET.getlist('selected_pcs')
            if not selected_pcs:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
                })
            
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
            selected_pcs = request.GET.getlist('selected_pcs')
            if not selected_pcs:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
                })
            
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
            selected_pcs = request.GET.getlist('selected_pcs')
            if not selected_pcs:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
                })
            
            if len(selected_pcs) > 1:
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'output': "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC."
                })
            
            pc_name = selected_pcs[0]
            rdp_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', f'{pc_name}.rdp')
            if os.path.exists(rdp_path):
                script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'OpenRDP.ps1')
                with open(script_path, "w") as f:
                    f.write(f'Start-Process "{rdp_path}"')
                result = run_powershell_command('schtasks /Run /TN "OpenRDP"')
                if "Error" in result:
                    output = f"Error al ejecutar la tarea programada: {result}"
                else:
                    output = f"Se ha iniciado la conexión de Escritorio Remoto a {pc_name}."
                    pc = Info_PCs.objects.get(nombre=pc_name)
                    pc.last_seen = timezone.now()
                    pc.save()
            else:
                output = f"Error: El archivo {pc_name}.rdp no existe en {os.path.join(settings.BASE_DIR, 'ScriptsPS')}."

    return render(request, 'control/control.html', {
        'online_pcs': online_pcs,
        'available_files': available_files,
        'output': output
    })