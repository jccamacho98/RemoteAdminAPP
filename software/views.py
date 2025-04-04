from django.shortcuts import render
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
import os
import uuid
from django.conf import settings  # Importar settings para usar BASE_DIR

def software(request):
    # Obtener solo los PCs que están Online
    online_pcs = Info_PCs.objects.filter(estado="Online").order_by('nombre')
    output = None
    show_rdp_prompt = False
    rdp_pc_name = None
    installer_path = None

    if request.method == "POST" and 'install_software' in request.POST:
        # Obtener los PCs seleccionados
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
            })

        # Determinar el tipo de instalación
        install_type = request.POST.get('install_type', 'unattended')  # Por defecto, desatendida
        unattended = (install_type == 'unattended')

        # Validar que solo se seleccione un PC en modo interactivo
        if not unattended and len(selected_pcs) > 1:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'output': "Error: La instalación interactiva solo permite seleccionar un PC a la vez."
            })

        # Obtener el archivo del instalador
        if 'installer_file' not in request.FILES:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'output': "Error: Por favor, seleccione un archivo instalador."
            })

        installer_file = request.FILES['installer_file']
        # Generar un nombre único para el archivo temporal
        temp_filename = f"{uuid.uuid4()}_{installer_file.name}"
        temp_installer_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'temp', temp_filename)

        # Crear el directorio temporal si no existe
        os.makedirs(os.path.dirname(temp_installer_path), exist_ok=True)

        # Guardar el archivo temporalmente
        try:
            with open(temp_installer_path, 'wb') as f:
                for chunk in installer_file.chunks():
                    f.write(chunk)
        except Exception as e:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'output': f"Error al guardar el archivo instalador: {str(e)}"
            })

        # Ruta de destino en el PC remoto
        remote_destination = f"C:\\Software\\{installer_file.name}"

        # Ejecutar el script para cada PC seleccionado
        script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'PruebaInstalarSoftware.ps1')
        output = []
        for pc_name in selected_pcs:
            # Construir los argumentos para el script
            args = f"{pc_name} \"{temp_installer_path}\" \"{remote_destination}\""
            if unattended:
                args += " -unattended"
            result = run_powershell_script(script_path, args=args)
            output.append(f"Resultado para {pc_name}:\n{result}\n")

            # Si es instalación interactiva, preparar la advertencia y la opción de RDP
            if not unattended:
                show_rdp_prompt = True
                rdp_pc_name = pc_name
                installer_path = remote_destination

        # Eliminar el archivo temporal después de usarlo
        try:
            os.remove(temp_installer_path)
        except Exception as e:
            output.append(f"Advertencia: No se pudo eliminar el archivo temporal {temp_installer_path}: {str(e)}\n")

        output = "\n".join(output)

    # Manejar la solicitud para iniciar una sesión RDP
    if request.method == "POST" and 'start_rdp' in request.POST:
        pc_name = request.POST.get('pc_name')
        if pc_name:
            rdp_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', f'{pc_name}.rdp')
            if os.path.exists(rdp_path):
                script_path = os.path.join(settings.BASE_DIR, 'ScriptsPS', 'OpenRDP.ps1')
                with open(script_path, "w") as f:
                    f.write(f'Start-Process "{rdp_path}"')
                result = run_powershell_command('schtasks /Run /TN "OpenRDP"')
                if "Error" in result:
                    output = f"Error al ejecutar la tarea programada para iniciar RDP: {result}"
                else:
                    output = f"Se ha iniciado la conexión de Escritorio Remoto a {pc_name}."
            else:
                output = f"Error: El archivo {pc_name}.rdp no existe en C:\WebAdminDev\ScriptsPS."

    return render(request, 'software/software.html', {
        'online_pcs': online_pcs,
        'output': output,
        'show_rdp_prompt': show_rdp_prompt,
        'rdp_pc_name': rdp_pc_name,
        'installer_path': installer_path
    })