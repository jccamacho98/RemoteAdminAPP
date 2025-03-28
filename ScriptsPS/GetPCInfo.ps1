# Script: GetPCInfo.ps1
param (
    [string]$PCName
)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Validar si se proporcionó el nombre del PC
if (-not $PCName) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

# Validar si el PC está en línea usando Test-Connection
Write-Output "Verificando si $PCName está en línea..."
try {
    $pingResult = Test-Connection -ComputerName $PCName -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        Write-Output "Status: Offline"
        Write-Output "Error: $PCName no está en línea."
        exit 0  # Salir con código 0 (éxito, pero no se obtuvo información porque no está en línea)
    }
    $status = "Online"
    Write-Output "$PCName está en línea. Obteniendo información..."
}
catch {
    Write-Output "Status: Offline"
    Write-Output "Error al verificar la conectividad con $PCName : $($_.Exception.Message)"
    exit 1  # Salir con código 1 (error)
}

# Si el PC está en línea, recolectar más información
try {
    # Crear una sesión WinRM para ejecutar comandos remotos
    $session = New-PSSession -ComputerName $PCName -Credential (New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList "SERVER331NB\Administrator", (ConvertTo-SecureString "Sala331server" -AsPlainText -Force)) -ErrorAction Stop

    # Obtener información del PC
    $ip = Invoke-Command -Session $session -ScriptBlock {
        $ipAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" }).IPAddress | Select-Object -First 1
        if (-not $ipAddress) { "N/A" } else { $ipAddress }
    }

    $mac = Invoke-Command -Session $session -ScriptBlock {
        $macAddress = (Get-NetAdapter | Where-Object { $_.Status -eq "Up" }).MacAddress | Select-Object -First 1
        if (-not $macAddress) { "N/A" } else { $macAddress }
    }

    $os = Invoke-Command -Session $session -ScriptBlock {
        $osCaption = (Get-CimInstance Win32_OperatingSystem).Caption
        if (-not $osCaption) { "N/A" } else { $osCaption }
    }

    $domainJoined = Invoke-Command -Session $session -ScriptBlock {
        (Get-CimInstance Win32_ComputerSystem).PartOfDomain
    }

    # Cerrar la sesión
    Remove-PSSession -Session $session

    # Devolver la información en un formato fácil de parsear
    Write-Output "Status: $status"
    Write-Output "IP: $ip"
    Write-Output "MAC: $mac"
    Write-Output "OS: $os"
    Write-Output "DomainJoined: $domainJoined"
}
catch {
    Write-Output "Status: Offline"
    Write-Output "Error al obtener información de $PCName : $($_.Exception.Message)"
    exit 1  # Salir con código 1 (error)
}