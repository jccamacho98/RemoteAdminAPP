from django.shortcuts import render
from scripts.models import Info_PCs
from scripts.utils import run_powershell_script, run_powershell_command
from django.utils import timezone
import os

def control(request):
    return render(request, 'control/control.html', {'output': None})

def shutdown_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control/control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ApagarPC.ps1"
    for pc_name in selected_pcs:
        result = run_powershell_script(script_path, args=pc_name)
        output.append(f"Resultado para {pc_name}:\n{result}\n")
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.estado = "Offline" if "Éxito" in result else "Offline"
        pc.last_seen = timezone.now()
        pc.save()
    return render(request, 'control/control.html', {'output': "\n".join(output)})

def restart_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control/control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    output = []
    script_path = r"C:\WebAdminDev\ScriptsPS\ReiniciarPC.ps1"
    for pc_name in selected_pcs:
        result = run_powershell_script(script_path, args=pc_name)
        output.append(f"Resultado para {pc_name}:\n{result}\n")
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.estado = "Online" if "Éxito" in result else "Offline"
        pc.last_seen = timezone.now()
        pc.save()
    return render(request, 'control/control.html', {'output': "\n".join(output)})

def remote_desktop_pc01(request):
    selected_pcs = request.GET.getlist('selected_pcs')
    if not selected_pcs:
        return render(request, 'control/control.html', {'output': "Error: Por favor, seleccione al menos un PC antes de realizar esta acción."})
    
    if len(selected_pcs) > 1:
        return render(request, 'control/control.html', {'output': "Aviso: No se pueden iniciar sesiones de Escritorio Remoto para múltiples PCs al mismo tiempo. Por favor, seleccione solo un PC."})
    
    pc_name = selected_pcs[0]
    rdp_path = f"C:\\WebAdminDev\\ScriptsPS\\{pc_name}.rdp"
    if os.path.exists(rdp_path):
        with open(r"C:\WebAdminDev\ScriptsPS\OpenRDP.ps1", "w") as f:
            f.write(f'Start-Process "C:\\WebAdminDev\\ScriptsPS\\{pc_name}.rdp"')
        output = run_powershell_command('schtasks /Run /TN "OpenRDP"')
        if "Error" in output:
            return render(request, 'control/control.html', {'output': f"Error al ejecutar la tarea programada: {output}"})
        pc = Info_PCs.objects.get(nombre=pc_name)
        pc.last_seen = timezone.now()
        pc.save()
        return render(request, 'control/control.html', {'output': f"Se ha iniciado la conexión de Escritorio Remoto a {pc_name}."})
    else:
        return render(request, 'control/control.html', {'output': f"Error: El archivo {pc_name}.rdp no existe en C:\WebAdminDev\ScriptsPS."})