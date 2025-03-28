# Script: InfoSoftwareInstalado.ps1
param (
    [string]$computer = $env:COMPUTERNAME  # Nombre del PC (por defecto, el equipo local)
)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Validar parámetros
if (-not $computer) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

# Credenciales para el PC remoto (ajusta según tu entorno)
$username = "SERVER331NB\administrator"  # Cambia según tu entorno
$password = "Sala331server"              # Cambia según tu entorno
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Validar si el PC está en línea usando Test-Connection
Write-Output "Verificando si $computer está en línea..."
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        Write-Output "$computer no está en línea. No se puede obtener la información de software."
        exit 0
    }
    Write-Output "$computer está en línea. Procediendo a obtener la lista de software instalado..."
}
catch {
    Write-Output "Error al verificar la conectividad con $computer : $($_.Exception.Message)"
    exit 1
}

# Función para obtener software instalado
function Get-InstalledSoftware {
    param ($session)
    $softwareList = Invoke-Command -Session $session -ScriptBlock {
        # Obtener software desde el registro (64-bit y 32-bit)
        $regPaths = @(
            "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
            "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
        )
        
        $installed = foreach ($path in $regPaths) {
            Get-ItemProperty -Path $path -ErrorAction SilentlyContinue | 
                Where-Object { $_.DisplayName } | 
                Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
        }
        
        # Devolver la lista ordenada por nombre
        $installed | Sort-Object DisplayName
    }
    return $softwareList
}

# Conectar al equipo remoto si no es el equipo local
if ($computer -ne $env:COMPUTERNAME) {
    try {
        $session = New-PSSession -ComputerName $computer -Credential $credential -ErrorAction Stop
        Write-Output "Conexión establecida con $computer."
    }
    catch {
        Write-Output "Error al conectar con $computer : $($_.Exception.Message)"
        exit 1
    }
    
    # Obtener software instalado
    try {
        $software = Get-InstalledSoftware -session $session
        if ($software) {
            Write-Output "Software instalado en $computer:"
            $software | Format-Table -AutoSize -Property DisplayName, DisplayVersion, Publisher, InstallDate
        } else {
            Write-Output "No se encontró software instalado o no hay información disponible en $computer."
        }
    }
    catch {
        Write-Output "Error al obtener la lista de software en $computer : $($_.Exception.Message)"
    }
    finally {
        Remove-PSSession $session -ErrorAction SilentlyContinue
        Write-Output "Conexión cerrada con $computer."
    }
} else {
    # Si es el equipo local, ejecutar directamente
    try {
        $software = Invoke-Command -ScriptBlock {
            $regPaths = @(
                "HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*",
                "HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*"
            )
            $installed = foreach ($path in $regPaths) {
                Get-ItemProperty -Path $path -ErrorAction SilentlyContinue | 
                    Where-Object { $_.DisplayName } | 
                    Select-Object DisplayName, DisplayVersion, Publisher, InstallDate
            }
            $installed | Sort-Object DisplayName
        }
        if ($software) {
            Write-Output "Software instalado en $computer (equipo local):"
            $software | Format-Table -AutoSize -Property DisplayName, DisplayVersion, Publisher, InstallDate
        } else {
            Write-Output "No se encontró software instalado o no hay información disponible en $computer."
        }
    }
    catch {
        Write-Output "Error al obtener la lista de software en $computer : $($_.Exception.Message)"
    }
}

Write-Output "Proceso finalizado."