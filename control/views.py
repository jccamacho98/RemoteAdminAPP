from django.shortcuts import render, redirect
from monitor.models import Info_PCs
from django.utils import timezone
import os
import uuid
from django.conf import settings
from django.http import JsonResponse
from django.contrib import messages
from celery.result import AsyncResult
from .tasks import copy_file_to_pcs, shutdown_pcs, restart_pcs
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async

async def send_pc_status_update():
    """Enviar actualización de la lista de PCs a todos los clientes conectados."""
    channel_layer = get_channel_layer()
    pcs = list(await sync_to_async(Info_PCs.objects.all)().values('nombre', 'estado'))
    await channel_layer.group_send(
        'pc_status',
        {
            'type': 'pc_status_update',
            'pcs': pcs,
        }
    )

async def send_warning(warning_message):
    """Enviar advertencia a todos los clientes conectados."""
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        'pc_status',
        {
            'type': 'warning_update',
            'warning': warning_message,
        }
    )

async def control(request):
    # Obtener solo los PCs que están Online (usando sync_to_async para la consulta a la base de datos)
    online_pcs = await sync_to_async(list)(
        Info_PCs.objects.filter(estado="Online").order_by('nombre')
    )

    # Listar los archivos disponibles en la carpeta SharedFiles (usando sync_to_async para operaciones de archivos)
    shared_files_dir = r"D:\SharedFiles"
    available_files = []
    if await sync_to_async(os.path.exists)(shared_files_dir):
        available_files = await sync_to_async(lambda: [f for f in os.listdir(shared_files_dir) if os.path.isfile(os.path.join(shared_files_dir, f))])()
    else:
        available_files = []
        await sync_to_async(messages.warning)(request, "Advertencia: La carpeta SharedFiles no existe en el servidor.")

    # Para solicitudes GET o después de una recarga, limpiar el estado de rdp_triggered
    if request.method == "GET":
        await sync_to_async(request.session.pop)('rdp_triggered', None)

    # Manejar la acción de copiar archivo (POST)
    if request.method == "POST" and 'copy_file' in request.POST:
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'No se seleccionaron PCs.'}, status=400)
            await sync_to_async(messages.error)(request, "Error: Por favor, seleccione al menos un PC antes de realizar esta acción.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        file_source = request.POST.get('file_source')
        source_file_path = None
        file_to_copy = None

        if file_source == "upload":
            if 'file_to_upload' not in request.FILES:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No se seleccionó ningún archivo para subir.'}, status=400)
                await sync_to_async(messages.error)(request, "Error: Por favor, seleccione un archivo para subir.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            file_to_copy = request.FILES['file_to_upload']
            max_file_size = 100 * 1024 * 1024
            if file_to_copy.size > max_file_size:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."}, status=400)
                await sync_to_async(messages.error)(request, f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            temp_filename = f"{uuid.uuid4()}_{file_to_copy.name}"
            temp_file_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'temp', temp_filename)
            await sync_to_async(os.makedirs)(os.path.dirname(temp_file_path), exist_ok=True)

            try:
                with open(temp_file_path, 'wb') as f:
                    for chunk in file_to_copy.chunks():
                        f.write(chunk)
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"Error al guardar el archivo temporal: {str(e)}"}, status=500)
                await sync_to_async(messages.error)(request, f"Error al guardar el archivo temporal: {str(e)}")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            if not await sync_to_async(os.path.exists)(temp_file_path) or await sync_to_async(os.path.getsize)(temp_file_path) == 0:
                try:
                    await sync_to_async(os.remove)(temp_file_path)
                except:
                    pass
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"No se pudo crear el archivo temporal en {temp_file_path} o está vacío."}, status=500)
                await sync_to_async(messages.error)(request, f"Error: No se pudo crear el archivo temporal en {temp_file_path} o está vacío.")
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
                await sync_to_async(messages.error)(request, "Error: Por favor, seleccione un archivo del servidor.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            file_to_copy_name = request.POST['file_from_server']
            source_file_path = os.path.join(shared_files_dir, file_to_copy_name)

            if not await sync_to_async(os.path.exists)(source_file_path) or await sync_to_async(os.path.getsize)(source_file_path) == 0:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo {file_to_copy_name} no existe o está vacío en el servidor."}, status=400)
                await sync_to_async(messages.error)(request, f"Error: El archivo {file_to_copy_name} no existe o está vacío en el servidor.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            if await sync_to_async(os.path.getsize)(source_file_path) > max_file_size:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': f"El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB."}, status=400)
                await sync_to_async(messages.error)(request, f"Error: El archivo es demasiado grande. El tamaño máximo permitido es {max_file_size / (1024 * 1024)} MB.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'Opción de fuente de archivo no válida.'}, status=400)
            await sync_to_async(messages.error)(request, "Error: Opción de fuente de archivo no válida.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'CopyFileToPC.ps1')
        task = copy_file_to_pcs.delay(selected_pcs, source_file_path, file_to_copy_name, script_path)

        if file_source == "upload":
            await sync_to_async(request.session.__setitem__)('temp_file_to_delete', source_file_path)

        return JsonResponse({'task_id': task.id})

    # Manejar las acciones de apagar, reiniciar y escritorio remoto (POST)
    if request.method == "POST":
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'error': 'No se seleccionaron PCs.'}, status=400)
            await sync_to_async(messages.error)(request, "Error: Por favor, seleccione al menos un PC antes de realizar esta acción.")
            return render(request, 'control/control.html', {
                'online_pcs': online_pcs,
                'available_files': available_files,
            })

        if 'shutdown' in request.POST:
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ApagarPC.ps1')
            task = shutdown_pcs.delay(selected_pcs, script_path)
            await send_pc_status_update()
            return JsonResponse({'task_id': task.id})

        elif 'restart' in request.POST:
            script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'ReiniciarPC.ps1')
            task = restart_pcs.delay(selected_pcs, script_path)
            await send_pc_status_update()
            return JsonResponse({'task_id': task.id})

        elif 'remote_desktop' in request.POST:
            if len(selected_pcs) > 1:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': 'No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC.'}, status=400)
                await sync_to_async(messages.warning)(request, "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC.")
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

            pc_name = selected_pcs[0]
            print(f"Iniciando proceso de Escritorio Remoto para el PC: {pc_name}")
            try:
                pc = await sync_to_async(Info_PCs.objects.get)(nombre=pc_name)
                print(f"Verificando estado del PC {pc_name}: {pc.estado}")
                if pc.estado != "Online":
                    error_msg = f"El PC {pc_name} está offline y no se puede iniciar una sesión de Escritorio Remoto."
                    print(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': error_msg}, status=400)
                    await sync_to_async(messages.error)(request, error_msg)
                    return render(request, 'control/control.html', {
                        'online_pcs': online_pcs,
                        'available_files': available_files,
                    })
                pc.last_seen = timezone.now()
                await sync_to_async(pc.save)()
                print(f"PC {pc_name} marcado como visto a las {pc.last_seen}")

                # Generar el archivo .rdp en el servidor
                rdp_folder = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'RDPFiles')
                rdp_path = os.path.join(rdp_folder, f"{pc_name}.rdp")
                trigger_file = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'TriggerRDP.txt')

                # Contenido del archivo .rdp con formato básico y sin credenciales
                rdp_content = f"""screen mode id:i:2
use multimon:i:0
desktopwidth:i:1280
desktopheight:i:720
session bpp:i:32
winposstr:s:0,3,0,0,800,600
compression:i:1
keyboardhook:i:2
audiocapturemode:i:0
videoplaybackmode:i:1
connection type:i:7
networkautodetect:i:1
bandwidthautodetect:i:1
displayconnectionbar:i:1
enableworkspacereconnect:i:0
disable wallpaper:i:0
allow font smoothing:i:0
allow desktop composition:i:0
disable full window drag:i:1
disable menu anims:i:1
disable themes:i:0
disable cursor setting:i:0
bitmapcachepersistenable:i:1
full address:s:{pc_name}
audiomode:i:0
redirectprinters:i:1
redirectcomports:i:0
redirectsmartcards:i:1
redirectclipboard:i:1
redirectposdevices:i:0
autoreconnection enabled:i:1
authentication level:i:2
prompt for credentials:i:0
negotiate security layer:i:1
remoteapplicationmode:i:0
alternate shell:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:0
gatewaybrokeringtype:i:0
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
drivestoredirect:s:
"""

                print(f"Creando directorio {rdp_folder} si no existe...")
                await sync_to_async(lambda: None if os.path.exists(rdp_folder) else os.makedirs(rdp_folder))()
                if not await sync_to_async(os.path.exists)(rdp_folder):
                    error_msg = f"No se pudo crear el directorio {rdp_folder}."
                    print(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': error_msg}, status=500)
                    await sync_to_async(messages.error)(request, error_msg)
                    return render(request, 'control/control.html', {
                        'online_pcs': online_pcs,
                        'available_files': available_files,
                    })

                print(f"Escribiendo archivo RDP en {rdp_path}...")
                try:
                    await sync_to_async(lambda: None)()  # Forzar contexto sincrónico
                    with open(rdp_path, 'w') as f:
                        f.write(rdp_content)
                except Exception as e:
                    error_msg = f"Error al escribir el archivo RDP: {str(e)}"
                    print(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': error_msg}, status=500)
                    await sync_to_async(messages.error)(request, error_msg)
                    return render(request, 'control/control.html', {
                        'online_pcs': online_pcs,
                        'available_files': available_files,
                    })

                print(f"Escribiendo nombre del PC {pc_name} en {trigger_file}...")
                try:
                    await sync_to_async(lambda: None)()  # Forzar contexto sincrónico
                    with open(trigger_file, 'w') as f:
                        f.write(pc_name)
                    # Verificar que el archivo se escribió correctamente
                    if await sync_to_async(os.path.exists)(trigger_file):
                        written_content = await sync_to_async(lambda: open(trigger_file, 'r').read())()
                        print(f"Contenido escrito en {trigger_file}: {written_content}")
                    else:
                        error_msg = f"No se pudo verificar la existencia de {trigger_file} después de escribir."
                        print(error_msg)
                        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                            return JsonResponse({'error': error_msg}, status=500)
                        await sync_to_async(messages.error)(request, error_msg)
                        return render(request, 'control/control.html', {
                            'online_pcs': online_pcs,
                            'available_files': available_files,
                        })
                except Exception as e:
                    error_msg = f"Error al escribir en TriggerRDP.txt: {str(e)}"
                    print(error_msg)
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return JsonResponse({'error': error_msg}, status=500)
                    await sync_to_async(messages.error)(request, error_msg)
                    return render(request, 'control/control.html', {
                        'online_pcs': online_pcs,
                        'available_files': available_files,
                    })

                print(f"Sesión de Escritorio Remoto solicitada para {pc_name}. La sesión se iniciará en breve.")
                # Guardar trigger_rdp y rdp_triggered en la sesión
                await sync_to_async(request.session.__setitem__)('trigger_rdp', pc_name)
                await sync_to_async(request.session.__setitem__)('rdp_triggered', True)
                # Redirigir para que se ejecute el bloque trigger_rdp en el template
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'message': f"Sesión de Escritorio Remoto solicitada para {pc_name}. La sesión se iniciará en breve.", 'redirect': '/control/'})
                return redirect('control')

            except Info_PCs.DoesNotExist:
                error_msg = f"El PC {pc_name} no existe en la base de datos."
                print(error_msg)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'error': error_msg}, status=400)
                await sync_to_async(messages.error)(request, error_msg)
                return render(request, 'control/control.html', {
                    'online_pcs': online_pcs,
                    'available_files': available_files,
                })

        # Manejar la limpieza de variables de sesión para RDP
        elif 'clear_rdp' in request.POST:
            await sync_to_async(request.session.pop)('trigger_rdp', None)
            await sync_to_async(request.session.pop)('rdp_triggered', None)
            return JsonResponse({'status': 'success', 'message': 'Variables de sesión RDP limpiadas.'})

    return render(request, 'control/control.html', {
        'online_pcs': online_pcs,
        'available_files': available_files,
        'trigger_rdp': request.session.get('trigger_rdp'),
        'rdp_triggered': request.session.get('rdp_triggered', False),
    })

async def get_task_status(request):
    task_id = request.GET.get('task_id')
    if not task_id:
        return JsonResponse({'status': 'error', 'message': 'No se proporcionó un ID de tarea.'})

    task = AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {'status': 'pending', 'message': 'La tarea está en curso...'}
    elif task.state == 'SUCCESS':
        results = task.result
        temp_file_to_delete = await sync_to_async(request.session.get)('temp_file_to_delete')
        if temp_file_to_delete and await sync_to_async(os.path.exists)(temp_file_to_delete):
            try:
                await sync_to_async(os.remove)(temp_file_to_delete)
                await sync_to_async(request.session.__delitem__)('temp_file_to_delete')
            except Exception as e:
                print(f"Error al eliminar el archivo temporal: {e}")
        response = {'status': 'success', 'results': results}
        await send_pc_status_update()
    else:
        response = {'status': 'error', 'message': f'La tarea falló: {str(task.result)}'}
        await send_warning(f"Tarea fallida: {str(task.result)}")
    return JsonResponse(response)

from django.utils.decorators import sync_and_async_middleware
control = sync_and_async_middleware(control)
get_task_status = sync_and_async_middleware(get_task_status)