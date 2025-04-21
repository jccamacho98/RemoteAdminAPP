from django.shortcuts import render, redirect
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
from django.utils import timezone
import os
import uuid
from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.contrib import messages
from celery.result import AsyncResult
from .tasks import copy_file_to_pcs, shutdown_pcs, restart_pcs

def control(request):
    # Obtener solo los PCs que están Online
    online_pcs = Info_PCs.objects.filter(estado="Online").order_by('nombre')

    # Listar los archivos disponibles en la carpeta SharedFiles
    shared_files_dir = r"D:\SharedFiles"
    available_files = []
    if os.path.exists(shared_files_dir):
        available_files = [f for f in os.listdir(shared_files_dir) if os.path.isfile(os.path.join(shared_files_dir, f))]
    else:
        available_files = []
        messages.warning(request, "Advertencia: La carpeta SharedFiles no existe en el servidor.")

    # Inicializar trigger_rdp como None por defecto
    trigger_rdp = None

    # Para solicitudes GET o después de una recarga, limpiar el estado de rdp_triggered
    if request.method == "GET":
        request.session.pop('rdp_triggered', None)

    # Manejar la acción de copiar archivo (POST)
    if request.method == "POST" and 'copy_file' in request.POST:
        print("Entrando en copy_file")  # Depuración
        selected_pcs = request.POST.getlist('selected_pcs')
        print(f"Selected PCs: {selected_pcs}")  # Depuración
        if not selected_pcs:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'No se seleccionaron PCs.'}, status=400)
            messages.error(request, "Error: Por favor, seleccione al menos un PC antes de realizar esta acción.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        # Determinar la fuente del archivo (subir o seleccionar del servidor)
        file_source = request.POST.get('file_source')
        source_file_path = None
        file_to_copy = None

        if file_source == "upload":
            if 'file_to_upload' not in request.FILES:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No se seleccionó ningún archivo para subir.'}, status=400)
                messages.error(request, "Error: Por favor, seleccione un archivo para subir.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            file_to_copy = request.FILES['file_to_upload']
            
            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if file_to_copy.size > max_file_size:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."}, status=400)
                messages.error(request, f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            temp_filename = f"{uuid.uuid4()}_{file_to_copy.name}"
            temp_file_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'temp', temp_filename)
            os.makedirs(os.path.dirname(temp_file_path), exist_ok=True)

            try:
                with open(temp_file_path, 'wb') as f:
                    for chunk in file_to_copy.chunks():
                        f.write(chunk)
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"Error al guardar el archivo temporal: {str(e)}"}, status=500)
                messages.error(request, f"Error al guardar el archivo temporal: {str(e)}")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            if not os.path.exists(temp_file_path):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"No se pudo crear el archivo temporal en {temp_file_path}."}, status=500)
                messages.error(request, f"Error: No se pudo crear el archivo temporal en {temp_file_path}.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            if os.path.getsize(temp_file_path) == 0:
                try:
                    os.remove(temp_file_path)
                except:
                    pass
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo temporal {temp_file_path} está vacío."}, status=400)
                messages.error(request, f"Error: El archivo temporal {temp_file_path} está vacío.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            source_file_path = temp_file_path
            file_to_copy_name = file_to_copy.name

        elif file_source == "server":
            if 'file_from_server' not in request.POST or not request.POST['file_from_server']:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No se seleccionó ningún archivo del servidor.'}, status=400)
                messages.error(request, "Error: Por favor, seleccione un archivo del servidor.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            file_to_copy_name = request.POST['file_from_server']
            source_file_path = os.path.join(shared_files_dir, file_to_copy_name)

            if not os.path.exists(source_file_path):
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo {file_to_copy_name} no existe en el servidor."}, status=400)
                messages.error(request, f"Error: El archivo {file_to_copy_name} no existe en el servidor.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            max_file_size = 100 * 1024 * 1024  # 100 MB en bytes
            if os.path.getsize(source_file_path) > max_file_size:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."}, status=400)
                messages.error(request, f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            if os.path.getsize(source_file_path) == 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo {file_to_copy_name} está vacío."}, status=400)
                messages.error(request, f"Error: El archivo {file_to_copy_name} está vacío.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Opción de fuente de archivo no válida.'}, status=400)
            messages.error(request, "Error: Opción de fuente de archivo no válida.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        # Iniciar la tarea de copia de archivos en segundo plano
        script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'CopyFileToPC.ps1')
        task = copy_file_to_pcs.delay(selected_pcs, source_file_path, file_to_copy_name, script_path)

        # Si el archivo es subido, lo eliminaremos después de iniciar la tarea
        if file_source == "upload":
            # Guardamos la ruta del archivo temporal en la sesión para eliminarlo después
            request.session['temp_file_to_delete'] = source_file_path

        # Devolver el ID de la tarea para que el frontend pueda consultar su estado
        return JsonResponse({'task_id': task.id})

    # Manejar las acciones de apagar, reiniciar y escritorio remoto (POST)
    if request.method == "POST":
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'No se seleccionaron PCs.'}, status=400)
            messages.error(request, "Error: Por favor, seleccione al menos un PC antes de realizar esta acción.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        if 'shutdown' in request.POST:
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ApagarPC.ps1')
            task = shutdown_pcs.delay(selected_pcs, script_path)
            return JsonResponse({'task_id': task.id})

        elif 'restart' in request.POST:
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ReiniciarPC.ps1')
            task = restart_pcs.delay(selected_pcs, script_path)
            return JsonResponse({'task_id': task.id})

        elif 'remote_desktop' in request.POST:
            if len(selected_pcs) > 1:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC.'}, status=400)
                messages.warning(request, "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })
    
            pc_name = selected_pcs[0]
            rdp_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', f'{pc_name}.rdp')
            if os.path.exists(rdp_path):
                try:
                    pc = Info_PCs.objects.get(nombre=pc_name)
                    if pc.estado != "Online":
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'error': f"El PC {pc_name} está offline y no se puede iniciar una sesión de Escritorio Remoto."}, status=400)
                        messages.error(request, f"El PC {pc_name} está offline y no se puede iniciar una sesión de Escritorio Remoto.")
                        return render(request, 'control/control.html', {
                            'online_pcs': online_pcs,
                            'available_files': available_files,
                        })
                    pc.last_seen = timezone.now()
                    pc.save()
                    # Establecer trigger_rdp y marcar en la sesión que ya se ha disparado
                    request.session['rdp_triggered'] = True
                    trigger_rdp = pc_name
                except Info_PCs.DoesNotExist:
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': f"El PC {pc_name} no existe en la base de datos."}, status=400)
                    messages.error(request, f"Error: El PC {pc_name} no existe en la base de datos.")
                    return render(request, 'control/control.html', {
                        'online_pcs': online_pcs,
                        'available_files': available_files,
                    })
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                    'trigger_rdp': trigger_rdp
                })
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo {pc_name}.rdp no existe en {os.path.join(settings.BASE_DIR, 'ScriptsPS')}."}, status=400)
                messages.error(request, f"Error: El archivo {pc_name}.rdp no existe en {os.path.join(settings.BASE_DIR, 'ScriptsPS')}.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

    # Si no hay acción, renderizar la página de control
    return render(request, 'control/control.html', {
        'online_pcs': online_pcs,
        'available_files': available_files,
    })

def get_task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'status': 'error', 'message': 'No se proporcionó un ID de tarea.'})

    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'status': 'pending', 'message': 'La tarea está en curso...'}
    elif task.state == 'SUCCESS':
        results = task.result
        # Eliminar el archivo temporal si existe en la sesión (solo para copy_file)
        temp_file_to_delete = request.session.get('temp_file_to_delete')
        if temp_file_to_delete and os.path.exists(temp_file_to_delete):
            try:
                os.remove(temp_file_to_delete)
                del request.session['temp_file_to_delete']
            except Exception as e:
                print(f"Error al eliminar el archivo temporal: {e}")
        response = {'status': 'success', 'results': results}
    else:
        response = {'status': 'error', 'message': f'La tarea falló: {str(task.result)}'}
    return JsonResponse(response)

def download_rdp(request, pc_name):
    rdp_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', f'{pc_name}.rdp')
    online_pcs = Info_PCs.objects.filter(estado="Online").order_by('nombre')
    shared_files_dir = r"D:\SharedFiles"
    available_files = [f for f in os.listdir(shared_files_dir) if os.path.isfile(os.path.join(shared_files_dir, f))] if os.path.exists(shared_files_dir) else []
    if os.path.exists(rdp_path):
        return FileResponse(
            open(rdp_path, 'rb'),
            as_attachment=True,
            filename=f'{pc_name}.rdp'
        )
    else:
        messages.error(request, f"Error: El archivo {pc_name}.rdp no existe en {os.path.join(settings.BASE_DIR, 'ScriptsPS')}.")
        return render(request, 'control/control.html', {
            'online_pcs': online_pcs,
            'available_files': available_files,
        })