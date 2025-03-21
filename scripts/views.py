from django.shortcuts import render
import winrm
import os
from requests.exceptions import Timeout

def run_powershell_script(script_path, args=""):
    try:
        session = winrm.Session(
            'http://192.168.128.31:5985/wsman',  # IP de Server331
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
            'http://192.168.128.31:5985/wsman',  # IP de Server331
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

def index(request):
    pcs = [{'name': 'PC01', 'status': 'En línea'}]
    all_pcs = [{'name': f'PC{i:02d}', 'status': 'No unido al dominio'} for i in range(1, 21)]
    for pc in pcs:
        index = int(pc['name'].replace('PC', '')) - 1
        all_pcs[index] = pc

    col1_pcs = all_pcs[0:5]
    col2_pcs = all_pcs[5:10]
    col3_pcs = all_pcs[10:15]
    col4_pcs = all_pcs[15:20]

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
    pcs = [{'name': 'PC01', 'status': 'En línea'}]
    all_pcs = [{'name': f'PC{i:02d}', 'status': 'No unido al dominio'} for i in range(1, 21)]
    for pc in pcs:
        index = int(pc['name'].replace('PC', '')) - 1
        all_pcs[index] = pc
    col1_pcs = all_pcs[0:5]
    col2_pcs = all_pcs[5:10]
    col3_pcs = all_pcs[10:15]
    col4_pcs = all_pcs[15:20]
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
    pcs = [{'name': 'PC01', 'status': 'En línea'}]
    all_pcs = [{'name': f'PC{i:02d}', 'status': 'No unido al dominio'} for i in range(1, 21)]
    for pc in pcs:
        index = int(pc['name'].replace('PC', '')) - 1
        all_pcs[index] = pc
    col1_pcs = all_pcs[0:5]
    col2_pcs = all_pcs[5:10]
    col3_pcs = all_pcs[10:15]
    col4_pcs = all_pcs[15:20]
    return render(request, 'index.html', {
        'col1_pcs': col1_pcs,
        'col2_pcs': col2_pcs,
        'col3_pcs': col3_pcs,
        'col4_pcs': col4_pcs,
        'output': output
    })

def shutdown_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')  # Obtener lista de PCs seleccionados
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ApagarPC.ps1"
    for pc in selected_pcs:
        result = run_powershell_script(script_path, args=pc)
        output.append(f"Resultado para {pc}:\n{result}\n")
    return render(request, 'control.html', {'output': "\n".join(output)})

def restart_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')  # Obtener lista de PCs seleccionados
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ReiniciarPC.ps1"
    for pc in selected_pcs:
        result = run_powershell_script(script_path, args=pc)
        output.append(f"Resultado para {pc}:\n{result}\n")
    return render(request, 'control.html', {'output': "\n".join(output)})

def remote_desktop_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')  # Obtener lista de PCs seleccionados
    if not selected_pcs:
        return render(request, 'control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    # Aviso si se seleccionan múltiples PCs para Escritorio Remoto
    if len(selected_pcs) > 1:
        return render(request, 'control.html', {'output': "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC."})
    
    # Si solo se seleccionó un PC, proceder con Escritorio Remoto
    pc = selected_pcs[0]
    rdp_path = f"C:\\WebAdminDev\\ScriptsPS\\{pc}.rdp"
    if os.path.exists(rdp_path):
        # Modificar el script OpenRDP.ps1 para usar el PC seleccionado
        with open(r"C:\WebAdminDev\ScriptsPS\OpenRDP.ps1", "w") as f:
            f.write(f'Start-Process "C:\\WebAdminDev\\ScriptsPS\\{pc}.rdp"')
        # Ejecutar la tarea programada OpenRDP
        output = run_powershell_command('schtasks /Run /TN "OpenRDP"')
        if "Error" in output:
            return render(request, 'control.html', {'output': f"Error al ejecutar la tarea programada: {output}"})
        return render(request, 'control.html', {'output': f"Se ha iniciado la conexión de Escritorio Remoto a {pc}."})
    else:
        return render(request, 'control.html', {'output': f"Error: El archivo {pc}.rdp no existe en C:\WebAdminDev\ScriptsPS."})

def monitor(request):
    return render(request, 'monitor.html')

def software(request):
    return render(request, 'software.html')

def control(request):
    return render(request, 'control.html', {'output': None})