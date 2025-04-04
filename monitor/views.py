import winrm
import os
import json
from django.shortcuts import render
from django.utils import timezone
from monitor.models import Info_PCs, SoftwareInstalado
from scripts.utils import update_pc_info  # Eliminamos update_pc_status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from scripts.serializers import InfoPCSerializer

# Función auxiliar para ejecutar scripts de PowerShell
def run_powershell_script(script_path, computer_name):
    try:
        # Leer las credenciales desde variables de entorno
        username = os.getenv('WINRM_USERNAME')
        password = os.getenv('WINRM_PASSWORD')

        if not username or not password:
            raise ValueError("Las credenciales no están configuradas en las variables de entorno.")

        # Crear una sesión WinRM en Server331 (localhost)
        session = winrm.Session(
            'http://localhost:5985/wsman',
            auth=(username, password),
            transport='ntlm'
        )
        
        # Convertir la ruta del script a una ruta absoluta (necesaria para PowerShell)
        script_path_absolute = os.path.abspath(script_path).replace('\\', '/')
        
        # Ejecutar el script directamente desde su ruta
        command = f'& "{script_path_absolute}" -computer "{computer_name}"'
        result = session.run_ps(command)
        
        # Verificar si hubo un error en std_err, pero ignorar mensajes de progreso
        if result.std_err:
            try:
                error_message = result.std_err.decode('utf-8')
            except UnicodeDecodeError:
                error_message = result.std_err.decode('latin-1')
            
            # Ignorar mensajes de progreso
            if "Preparing modules for first use" in error_message:
                error_message = None
            else:
                return None, f"Error al ejecutar el script: {error_message}"
        
        # Procesar la salida del script (esperamos JSON)
        try:
            output = result.std_out.decode('utf-8')
        except UnicodeDecodeError:
            output = result.std_out.decode('latin-1')
        
        try:
            result_json = json.loads(output)
            if result_json['status'] == 'success':
                return result_json['data'], None
            else:
                return None, result_json['message']
        except json.JSONDecodeError as e:
            return None, f"Error al parsear la salida del script como JSON: {str(e)}"
    except Exception as e:
        return None, f"Error al ejecutar el script: {str(e)}"

# Función para actualizar el software instalado en la base de datos
def update_software_info(pc):
    # Ruta al script InfoSoftwareInstalado.ps1
    script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scriptsPS', 'InfoSoftwareInstalado.ps1')
    
    # Ejecutar el script
    software_list, error = run_powershell_script(script_path, pc.nombre)
    
    if error:
        return error
    
    # Eliminar el software existente para este PC
    SoftwareInstalado.objects.filter(pc=pc).delete()
    
    # Guardar la nueva lista de software en la base de datos
    for software in software_list:
        SoftwareInstalado.objects.create(
            pc=pc,
            display_name=software.get('DisplayName', ''),
            display_version=software.get('DisplayVersion', ''),
            publisher=software.get('Publisher', ''),
            install_date=software.get('InstallDate', '')
        )
    
    return None

# Vista principal de monitor
def monitor(request):
    # No actualizamos el estado aquí; confiamos en el poller update_dynamic_data
    pcs = Info_PCs.objects.all().order_by('nombre')
    context = {'pcs': pcs, 'output': None, 'software_list': None, 'software_error': None, 'selected_pc': None}

    # Manejar la actualización de información
    if request.method == "POST" and 'update_info' in request.POST:
        context['output'] = update_pc_info()

    # Manejar la acción de listar software
    if request.method == "POST" and 'list_software' in request.POST:
        selected_pc = request.POST.get('selected_pc')
        if selected_pc:
            context['selected_pc'] = selected_pc
            try:
                pc = Info_PCs.objects.get(nombre=selected_pc)
                # Cargar la lista de software desde la base de datos
                software_list = pc.software_instalado.all()
                context['software_list'] = software_list
            except Info_PCs.DoesNotExist:
                context['software_error'] = f"El PC {selected_pc} no existe en la base de datos."

    # Manejar la acción de actualizar información del software
    if request.method == "POST" and 'update_software' in request.POST:
        selected_pc = request.POST.get('selected_pc')
        if selected_pc:
            context['selected_pc'] = selected_pc
            try:
                pc = Info_PCs.objects.get(nombre=selected_pc)
                # Solo actualizar si el PC está online
                if pc.estado == 'Online':
                    error = update_software_info(pc)
                    if error:
                        context['software_error'] = error
                    else:
                        context['software_list'] = pc.software_instalado.all()
                        context['software_message'] = f"Información del software actualizada para {selected_pc}."
                else:
                    context['software_error'] = f"No se puede actualizar la información porque {selected_pc} está offline."
            except Info_PCs.DoesNotExist:
                context['software_error'] = f"El PC {selected_pc} no existe en la base de datos."

    return render(request, 'monitor/monitor.html', context)

@api_view(['GET'])
def api_get_pcs(request):
    pcs = Info_PCs.objects.all().order_by('nombre')
    serializer = InfoPCSerializer(pcs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def api_update_info(request):
    output = update_pc_info() 
    return Response({'message': 'Actualización completada.', 'output': output})