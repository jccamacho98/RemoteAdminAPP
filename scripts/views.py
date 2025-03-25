from django.shortcuts import render
import winrm
import os
from requests.exceptions import Timeout
from scripts.models import Info_PCs
from django.utils import timezone

def run_powershell_script(script_path, args=""):
    try:
        session = winrm.Session(
            'http://192.168.128.31:5985/wsman',
            auth=('SERVER331NB\\Administrator', 'Sala331server'),
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
        session = winrm.Session(
            'http://192.168.128.31:5985/wsman',
            auth=('SERVER331NB\\Administrator', 'Sala331server'),
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

def update_pc_info():
    script_path = r"C:\WebAdminDev\ScriptsPS\GetPCInfo.ps1"
    pcs = Info_PCs.objects.all().order_by('nombre')
    output = []
    for pc in pcs:
        result = run_powershell_script(script_path, args=pc.nombre)
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
            elif line.startswith("MAC:"):
                mac = line.split("MAC: ")[1].strip()
            elif line.startswith("OS:"):
                os = line.split("OS: ")[1].strip()
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

def index(request):
    pcs = Info_PCs.objects.all().order_by('nombre')
    col1_pcs = pcs[0:5]
    col2_pcs = pcs[5:10]
    col3_pcs = pcs[10:15]
    col4_pcs = pcs[15:20]
    return render(request, 'index.html', {
        'col1_pcs': col1_pcs,
        'col2_pcs': col2_pcs,
        'col3_pcs': col3_pcs,
        'col4_pcs': col4_pcs,
        'output': None
    })

def install_7zip(request):
    script_path = r"C:\WebAdminDev\ScriptsPS\PruebaInstalarSoftware.ps1"
    output = run_powershell_script(script_path)
    pcs = Info_PCs.objects.all().order_by('nombre')
    col1_pcs = pcs[0:5]
    col2_pcs = pcs[5:10]
    col3_pcs = pcs[10:15]
    col4_pcs = pcs[15:20]
    return render(request, 'index.html', {
        'col1_pcs': col1_pcs,
        'col2_pcs': col2_pcs,
        'col3_pcs': col3_pcs,
        'col4_pcs': col4_pcs,
        'output': output
    })

def uninstall_7zip(request):
    script_path = r"C:\WebAdminDev\ScriptsPS\PruebaDesinstalarSoftware.ps1"
    output = run_powershell_script(script_path)
    pcs = Info_PCs.objects.all().order_by('nombre')
    col1_pcs = pcs[0:5]
    col2_pcs = pcs[5:10]
    col3_pcs = pcs[10:15]
    col4_pcs = pcs[15:20]
    return render(request, 'index.html', {
        'col1_pcs': col1_pcs,
        'col2_pcs': col2_pcs,
        'col3_pcs': col3_pcs,
        'col4_pcs': col4_pcs,
        'output': output
    })

def shutdown_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ApagarPC.ps1"
    for pc_name in selected_pcs:
        result = run_powershell_script(script_path, args=pc_name)
        output.append(f"Resultado para {pc_name}:\n{result}\n")
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.estado = "Offline" if "Éxito" in result else "Offline"
        pc.last_seen = timezone.now()
        pc.save()
    return render(request, 'control.html', {'output': "\n".join(output)})

def restart_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ReiniciarPC.ps1"
    for pc_name in selected_pcs:
        result = run_powershell_script(script_path, args=pc_name)
        output.append(f"Resultado para {pc_name}:\n{result}\n")
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.estado = "Online" if "Éxito" in result else "Offline"
        pc.last_seen = timezone.now()
        pc.save()
    return render(request, 'control.html', {'output': "\n".join(output)})

def remote_desktop_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    if len(selected_pcs) > 1:
        return render(request, 'control.html', {'output': "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC."})
    
    pc_name = selected_pcs[0]
    rdp_path = f"C:\\WebAdminDev\\ScriptsPS\\{pc_name}.rdp"
    if os.path.exists(rdp_path):
        with open(r"C:\WebAdminDev\ScriptsPS\OpenRDP.ps1", "w") as f:
            f.write(f'Start-Process "C:\\WebAdminDev\\ScriptsPS\\{pc_name}.rdp"')
        output = run_powershell_command('schtasks /Run /TN "OpenRDP"')
        if "Error" in output:
            return render(request, 'control.html', {'output': f"Error al ejecutar la tarea programada: {output}"})
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.last_seen = timezone.now()
        pc.save()
        return render(request, 'control.html', {'output': f"Se ha iniciado la conexión de Escritorio Remoto a {pc_name}."})
    else:
        return render(request, 'control.html', {'output': f"Error: El archivo {pc_name}.rdp no existe en C:\WebAdminDev\ScriptsPS."})

def monitor(request):
    pcs = Info_PCs.objects.all().order_by('nombre')
    output = None
    if request.method == "POST" and 'update_info' in request.POST:
        output = update_pc_info()
        pcs = Info_PCs.objects.all().order_by('nombre')  # Refrescar los datos después de actualizar
    return render(request, 'monitor.html', {'pcs': pcs, 'output': output})

def software(request):
    return render(request, 'software.html')

def control(request):
    return render(request, 'control.html', {'output': None})