from django.shortcuts import render
import winrm
import os
from requests.exceptions import Timeout

def run_powershell_script(script_path):
    try:
        session = winrm.Session(
            'http://localhost:5985/wsman',
            auth=('SERVER331NB\\Administrator', 'Sala331server'),
            transport='ntlm',
            operation_timeout_sec=5,
            read_timeout_sec=10
        )
        result = session.run_ps(f'powershell -File "{script_path}"')
        try:
            output = result.std_out.decode('utf-16-le')
        except UnicodeDecodeError:
            try:
                output = result.std_out.decode('utf-8')
            except UnicodeDecodeError:
                output = result.std_out.decode('windows-1252')
        error_output = result.std_err.decode('windows-1252', errors='replace')
        return output + error_output
    except Timeout:
        return "Error: El script tardó demasiado en responder (timeout)."
    except Exception as e:
        return f"Error al ejecutar el script: {str(e)}"

def index(request):
    return render(request, 'index.html', {'output': None})

def install_7zip(request):
    script_path = r"D:\ScriptsPS\PruebaInstalarSoftware.ps1"
    if os.path.exists(script_path):
        output = run_powershell_script(script_path)
        return render(request, 'index.html', {'output': output})
    return render(request, 'index.html', {'output': "Error: Script no encontrado en D:\ScriptsPS\PruebaInstalarSoftware.ps1"})

def uninstall_7zip(request):
    script_path = r"D:\ScriptsPS\PruebaDesinstalarSoftware.ps1"
    if os.path.exists(script_path):
        output = run_powershell_script(script_path)
        return render(request, 'index.html', {'output': output})
    return render(request, 'index.html', {'output': "Error: Script no encontrado en D:\ScriptsPS\PruebaDesinstalarSoftware.ps1"})

def shutdown_pc01(request):
    script_path = r"D:\ScriptsPS\ApagarPC.ps1"
    if os.path.exists(script_path):
        output = run_powershell_script(script_path)
        return render(request, 'index.html', {'output': output})
    return render(request, 'index.html', {'output': "Error: Script no encontrado en D:\ScriptsPS\ApagarPC.ps1"})
