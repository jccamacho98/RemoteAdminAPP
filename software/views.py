from django.shortcuts import render
from monitor.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
import os
import uuid
from django.conf import settings

def software(request):
    # Obtener solo los PCs que están Online
    online_pcs = Info_PCs.objects.filter(estado="Online").order_by('nombre')
    output = None
    show_rdp_prompt = False
    rdp_pc_name = None
    installer_path = None
    trigger_rdp = None

    # Limpiar el estado de rdp_triggered en solicitudes GET
    if request.method == "GET":
        request.session.pop('rdp_triggered', None)

    # Definir las rutas de las carpetas de software en D:\
    unattended_software_dir = r"D:\SoftwareInstalacionDesatendida"
    attended_software_dir = r"D:\SoftwareInstalacionAtendida"

    # Listar los archivos disponibles en las carpetas
    unattended_software_files = []
    attended_software_files = []
    
    # Archivos para instalación desatendida
    try:
        if os.path.exists(unattended_software_dir):
            unattended_software_files = [
                f for f in os.listdir(unattended_software_dir)
                if os.path.isfile(os.path.join(unattended_software_dir, f)) and f.lower().endswith(('.exe', '.msi'))
            ]
        else:
            output = f"Advertencia: La carpeta {unattended_software_dir} no existe."
    except Exception as e:
        output = f"Error al acceder a {unattended_software_dir}: {str(e)}"
    
    # Archivos para instalación atendida
    try:
        if os.path.exists(attended_software_dir):
            attended_software_files = [
                f for f in os.listdir(attended_software_dir)
                if os.path.isfile(os.path.join(attended_software_dir, f)) and f.lower().endswith(('.exe', '.msi'))
            ]
        else:
            if output:
                output += f"\nAdvertencia: La carpeta {attended_software_dir} no existe."
            else:
                output = f"Advertencia: La carpeta {attended_software_dir} no existe."
    except Exception as e:
        if output:
            output += f"\nError al acceder a {attended_software_dir}: {str(e)}"
        else:
            output = f"Error al acceder a {attended_software_dir}: {str(e)}"

    if request.method == "POST" and 'install_software' in request.POST:
        # Obtener los PCs seleccionados
        selected_pcs = request.POST.getlist('selected_pcs')
        if not selected_pcs:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'unattended_software_files': unattended_software_files,
                'attended_software_files': attended_software_files,
                'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."
            })

        # Determinar el tipo de instalación
        source_type = request.POST.get('source_type', 'upload')  # Por defecto, subir archivo
        if source_type == 'upload':
            install_type = request.POST.get('install_type', 'unattended')  # Por defecto, desatendida
            unattended = (install_type == 'unattended')
        else:
            # Deducir el tipo de instalación según la carpeta del archivo seleccionado
            server_file = request.POST.get('server_file')
            if server_file in unattended_software_files:
                unattended = True
            elif server_file in attended_software_files:
                unattended = False
            else:
                unattended = True  # Por defecto, desatendida si no se puede determinar

        # Validar que solo se seleccione un PC en modo interactivo
        if not unattended and len(selected_pcs) > 1:
            return render(request, 'software/software.html', {
                'online_pcs': online_pcs,
                'unattended_software_files': unattended_software_files,
                'attended_software_files': attended_software_files,
                'output': "Error: La instalación interactiva solo permite seleccionar un PC a la vez."
            })

        # Determinar la fuente del archivo (subido o desde el servidor)
        temp_installer_path = None

        if source_type == 'upload':
            # Subir archivo desde el cliente
            if 'installer_file' not in request.FILES:
                return render(request, 'software/software.html', {
                    'online_pcs': online_pcs,
                    'unattended_software_files': unattended_software_files,
                    'attended_software_files': attended_software_files,
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
                    'unattended_software_files': unattended_software_files,
                    'attended_software_files': attended_software_files,
                    'output': f"Error al guardar el archivo instalador: {str(e)}"
                })

            installer_filename = installer_file.name
        else:
            # Seleccionar archivo desde el servidor
            installer_filename = request.POST.get('server_file')
            if not installer_filename:
                return render(request, 'software/software.html', {
                    'online_pcs': online_pcs,
                    'unattended_software_files': unattended_software_files,
                    'attended_software_files': attended_software_files,
                    'output': "Error: Por favor, seleccione un archivo del servidor."
                })

            # Determinar la carpeta de origen según el tipo de instalación
            source_dir = unattended_software_dir if unattended else attended_software_dir
            temp_installer_path = os.path.join(source_dir, installer_filename)

            # Verificar que el archivo exista
            if not os.path.exists(temp_installer_path):
                return render(request, 'software/software.html', {
                    'online_pcs': online_pcs,
                    'unattended_software_files': unattended_software_files,
                    'attended_software_files': attended_software_files,
                    'output': f"Error: El archivo {installer_filename} no existe en el servidor."
                })

        # Ruta de destino en el PC remoto
        remote_destination = f"C:\\Software\\{installer_filename}"

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

        # Eliminar el archivo temporal si se subió desde el cliente
        if source_type == 'upload' and temp_installer_path and os.path.exists(temp_installer_path):
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
            if not os.path.exists(rdp_path):
                output = f"Error: El archivo {rdp_path} no existe. Por favor, crea el archivo RDP para {pc_name}."
            else:
                # Establecer trigger_rdp y marcar en la sesión que ya se ha disparado
                request.session['rdp_triggered'] = True
                trigger_rdp = pc_name
        else:
            output = "Error: No se proporcionó un nombre de PC para la conexión RDP."

    return render(request, 'software/software.html', {
        'online_pcs': online_pcs,
        'unattended_software_files': unattended_software_files,
        'attended_software_files': attended_software_files,
        'output': output,
        'show_rdp_prompt': show_rdp_prompt,
        'rdp_pc_name': rdp_pc_name,
        'installer_path': installer_path,
        'trigger_rdp': trigger_rdp
    })