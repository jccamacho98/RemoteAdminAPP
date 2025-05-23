from celery import shared_task
from scripts.utils import run_powershell_script
from monitor.models import Info_PCs
from django.utils import timezone
from channels.layers import get_channel_layer
import asyncio

@shared_task
def copy_file_to_pcs(selected_pcs, source_file_path, file_to_copy_name, script_path):
    results = []
    remote_destination = f"C:\\Archivos compartidos Server\\{file_to_copy_name}"
    channel_layer = get_channel_layer()

    # Definir una función asíncrona para enviar mensajes WebSocket
    async def send_warning(warning_message):
        await channel_layer.group_send(
            'pc_status',
            {
                'type': 'warning_update',
                'warning': warning_message,
            }
        )

    for pc_name in selected_pcs:
        try:
            # Verificar si el PC existe y está en línea
            pc = Info_PCs.objects.get(nombre=pc_name)
            if pc.estado != "Online":
                error_message = f"El PC {pc_name} está offline y no se puede copiar el archivo."
                results.append({"pc": pc_name, "status": "error", "message": error_message})
                # Enviar advertencia a través de WebSocket
                asyncio.run(send_warning(error_message))
                continue
        except Info_PCs.DoesNotExist:
            error_message = f"El PC {pc_name} no existe en la base de datos."
            results.append({"pc": pc_name, "status": "error", "message": error_message})
            # Enviar advertencia a través de WebSocket
            asyncio.run(send_warning(error_message))
            continue

        # Preparar los argumentos para el script de PowerShell
        source_file_path = source_file_path.replace('/', '\\')
        remote_destination = remote_destination.replace('/', '\\')
        args = f'"{pc_name}" "{source_file_path}" "{remote_destination}"'
        result = run_powershell_script(script_path, args=args)

        # Procesar el resultado del script
        if "Archivo copiado exitosamente" in result:
            results.append({"pc": pc_name, "status": "success", "message": f"Archivo copiado exitosamente a {remote_destination}"})
        else:
            results.append({"pc": pc_name, "status": "error", "message": result})
            # Enviar advertencia a través de WebSocket
            asyncio.run(send_warning(f"Error al copiar archivo a {pc_name}: {result}"))

    return results

@shared_task
def shutdown_pcs(pc_list, script_path):
    print(f"Starting shutdown_pcs with pc_list={pc_list}")
    results = []
    channel_layer = get_channel_layer()

    # Definir funciones asíncronas para enviar mensajes WebSocket
    async def send_warning(warning_message):
        await channel_layer.group_send(
            'pc_status',
            {
                'type': 'warning_update',
                'warning': warning_message,
            }
        )

    async def send_pc_status_update(pcs_data):
        await channel_layer.group_send(
            'pc_status',
            {
                'type': 'pc_status_update',
                'pcs': pcs_data,
            }
        )

    for pc in pc_list:
        try:
            print(f"Apagando {pc}...")
            # Verificar si el PC está en línea
            try:
                pc_obj = Info_PCs.objects.get(nombre=pc)
                if pc_obj.estado != "Online":
                    print(f"{pc} no está en línea. Saltando...")
                    error_message = f"{pc} no está en línea."
                    results.append({"pc": pc, "status": "error", "message": error_message})
                    # Enviar advertencia a través de WebSocket
                    asyncio.run(send_warning(error_message))
                    continue
            except Info_PCs.DoesNotExist:
                print(f"El PC {pc} no existe en la base de datos.")
                error_message = f"El PC {pc} no existe en la base de datos."
                results.append({"pc": pc, "status": "error", "message": error_message})
                # Enviar advertencia a través de WebSocket
                asyncio.run(send_warning(error_message))
                continue

            # Ejecutar el script de PowerShell para apagar el PC
            output = run_powershell_script(script_path, args=f'"{pc}"')
            if "Éxito" in output:
                print(f"{pc} apagado exitosamente.")
                # Actualizar el estado en la base de datos
                pc_obj.estado = "Offline"
                pc_obj.last_seen = timezone.now()
                pc_obj.save()
                results.append({"pc": pc, "status": "success", "message": f"{pc} apagado exitosamente."})
            else:
                print(f"Error al apagar {pc}: {output}")
                results.append({"pc": pc, "status": "error", "message": output})
                # Enviar advertencia a través de WebSocket
                asyncio.run(send_warning(f"Error al apagar {pc}: {output}"))

        except Exception as e:
            print(f"Error al apagar {pc}: {str(e)}")
            error_message = f"Error al apagar {pc}: {str(e)}"
            results.append({"pc": pc, "status": "error", "message": error_message})
            # Enviar advertencia a través de WebSocket
            asyncio.run(send_warning(error_message))

    # Enviar actualización de la lista de PCs después de completar la tarea
    pcs = list(Info_PCs.objects.all().values('nombre', 'estado'))
    asyncio.run(send_pc_status_update(pcs))

    print(f"Tarea completada con resultados: {results}")
    return results

@shared_task
def restart_pcs(pc_list, script_path):
    print(f"Starting restart_pcs with pc_list={pc_list}")
    results = []
    channel_layer = get_channel_layer()

    # Definir funciones asíncronas para enviar mensajes WebSocket
    async def send_warning(warning_message):
        await channel_layer.group_send(
            'pc_status',
            {
                'type': 'warning_update',
                'warning': warning_message,
            }
        )

    async def send_pc_status_update(pcs_data):
        await channel_layer.group_send(
            'pc_status',
            {
                'type': 'pc_status_update',
                'pcs': pcs_data,
            }
        )

    for pc in pc_list:
        try:
            print(f"Reiniciando {pc}...")
            # Verificar si el PC está en línea
            try:
                pc_obj = Info_PCs.objects.get(nombre=pc)
                if pc_obj.estado != "Online":
                    print(f"{pc} no está en línea. Saltando...")
                    error_message = f"{pc} no está en línea."
                    results.append({"pc": pc, "status": "error", "message": error_message})
                    # Enviar advertencia a través de WebSocket
                    asyncio.run(send_warning(error_message))
                    continue
            except Info_PCs.DoesNotExist:
                print(f"El PC {pc} no existe en la base de datos.")
                error_message = f"El PC {pc} no existe en la base de datos."
                results.append({"pc": pc, "status": "error", "message": error_message})
                # Enviar advertencia a través de WebSocket
                asyncio.run(send_warning(error_message))
                continue

            # Ejecutar el script de PowerShell para reiniciar el PC
            output = run_powershell_script(script_path, args=f'"{pc}"')
            if "Éxito" in output:
                print(f"{pc} reiniciado exitosamente.")
                # Actualizar el estado en la base de datos
                pc_obj.estado = "Offline"
                pc_obj.last_seen = timezone.now()
                pc_obj.save()
                results.append({"pc": pc, "status": "success", "message": f"{pc} reiniciado exitosamente."})
            else:
                print(f"Error al reiniciar {pc}: {output}")
                results.append({"pc": pc, "status": "error", "message": output})
                # Enviar advertencia a través de WebSocket
                asyncio.run(send_warning(f"Error al reiniciar {pc}: {output}"))

        except Exception as e:
            print(f"Error al reiniciar {pc}: {str(e)}")
            error_message = f"Error al reiniciar {pc}: {str(e)}"
            results.append({"pc": pc, "status": "error", "message": error_message})
            # Enviar advertencia a través de WebSocket
            asyncio.run(send_warning(error_message))

    # Enviar actualización de la lista de PCs después de completar la tarea
    pcs = list(Info_PCs.objects.all().values('nombre', 'estado'))
    asyncio.run(send_pc_status_update(pcs))

    print(f"Tarea completada con resultados: {results}")
    return results