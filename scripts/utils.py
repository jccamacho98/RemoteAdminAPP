import winrm
from requests.exceptions import Timeout
from monitor.models import Info_PCs
from django.utils import timezone
import os
from django.conf import settings  # Importar settings para obtener BASE_DIR

def run_powershell_script(script_path, args=""):
    try:
        # Leer credenciales desde variables de entorno
        username = os.getenv('WINRM_USERNAME')
        password = os.getenv('WINRM_PASSWORD')
        if not username or not password:
            return "Error: Las variables de entorno WINRM_USERNAME y WINRM_PASSWORD deben estar definidas."

        session = winrm.Session(
            'http://192.168.128.31:5985/wsman',
            auth=(username, password),
            transport='ntlm',
            operation_timeout_sec=5,
            read_timeout_sec=10
        )
        command = f'powershell -File "{script_path}" {args}'
        result = session.run_ps(command)
        try:
            output = result.std_out.decode('utf-8')
        except UnicodeDecodeError:
            try:
                output = result.std_out.decode('utf-16-le')
            except UnicodeDecodeError:
                output = result.std_out.decode('windows-1252', errors='replace')
        error_output = result.std_err.decode('windows-1252', errors='replace')
        if error_output:
            return f"Error en el script: {error_output}"
        return output
    except Timeout:
        return "Error: El script tardó demasiado en responder (timeout)."
    except Exception as e:
        return f"Error al ejecutar el script: {str(e)}"

def run_powershell_command(command):
    try:
        # Leer credenciales desde variables de entorno
        username = os.getenv('WINRM_USERNAME')
        password = os.getenv('WINRM_PASSWORD')
        if not username or not password:
            return "Error: Las variables de entorno WINRM_USERNAME y WINRM_PASSWORD deben estar definidas."

        session = winrm.Session(
            'http://192.168.128.31:5985/wsman',
            auth=(username, password),
            transport='ntlm',
            operation_timeout_sec=5,
            read_timeout_sec=10
        )
        result = session.run_ps(command)
        try:
            output = result.std_out.decode('utf-8')
        except UnicodeDecodeError:
            try:
                output = result.std_out.decode('utf-16-le')
            except UnicodeDecodeError:
                output = result.std_out.decode('windows-1252', errors='replace')
        error_output = result.std_err.decode('windows-1252', errors='replace')
        if error_output:
            return f"Error en el comando: {error_output}"
        return output
    except Timeout:
        return "Error: El comando tardó demasiado en responder (timeout)."
    except Exception as e:
        return f"Error al ejecutar el comando: {str(e)}"

def update_pc_status():
    pcs = Info_PCs.objects.all().order_by('nombre')
    for pc in pcs:
        try:
            session = winrm.Session(
                f'http://{pc.nombre}.Server331.local:5985/wsman',
                auth=('SERVER331NB\\Administrator', 'Sala331server'),
                transport='ntlm',
                operation_timeout_sec=0.5,
                read_timeout_sec=1
            )
            session.protocol.get_session()
            pc.estado = "Online"
        except Exception:
            pc.estado = "Offline"
        pc.last_seen = timezone.now()
        pc.save()

def update_pc_info():
    # Usar settings.BASE_DIR para obtener el directorio raíz del proyecto
    project_root = settings.BASE_DIR
    script_path = os.path.join(project_root, 'ScriptsPS', 'GetPCInfo.ps1')
    
    pcs = Info_PCs.objects.all().order_by('nombre')
    output = []
    for pc in pcs:
        result = run_powershell_script(script_path, args=f'"{pc.nombre}"')
        output.append(f"Resultado para {pc.nombre}:\n{result}\n")
        
        # Parsear la salida del script
        status = "Offline"
        ip = None
        mac = None
        os = None
        domain_joined = False
        
        for line in result.splitlines():
            if line.startswith("Status:"):
                status = line.split("Status: ")[1].strip()
            elif line.startswith("IP:"):
                ip = line.split("IP: ")[1].strip()
                if ip == "N/A":
                    ip = None
            elif line.startswith("MAC:"):
                mac = line.split("MAC: ")[1].strip()
                if mac == "N/A":
                    mac = None
            elif line.startswith("OS:"):
                os = line.split("OS: ")[1].strip()
                if os == "N/A":
                    os = None
            elif line.startswith("DomainJoined:"):
                domain_joined = line.split("DomainJoined: ")[1].strip().lower() == "true"
            elif line.startswith("Error:"):
                output.append(f"Error al obtener información de {pc.nombre}: {line}")
                continue
        
        # Actualizar el registro existente
        pc.estado = status
        pc.ip = ip
        pc.mac_address = mac
        pc.sistema_operativo = os
        pc.domain_joined = domain_joined
        pc.last_seen = timezone.now()
        pc.save()
    
    return "\n".join(output)