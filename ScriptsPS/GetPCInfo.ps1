param (
    [string]$PCName
)

# Verificar si el PC está en línea usando Test-WSMan
try {
    $wsmanTest = Test-WSMan -ComputerName $PCName -ErrorAction Stop
    $status = "Online"
}
catch {
    $status = "Offline"
    Write-Output "Status: $status"
    exit
}

# Si el PC está en línea, recolectar más información
try {
    # Crear una sesión WinRM para ejecutar comandos remotos
    $session = New-PSSession -ComputerName $PCName -Credential (New-Object -TypeName System.Management.Automation.PSCredential -ArgumentList "SERVER331NB\Administrator", (ConvertTo-SecureString "Sala331server" -AsPlainText -Force)) -ErrorAction Stop

    # Obtener información del PC
    $ip = Invoke-Command -Session $session -ScriptBlock {
        (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.*" }).IPAddress | Select-Object -First 1
    }

    $mac = Invoke-Command -Session $session -ScriptBlock {
        (Get-NetAdapter | Where-Object { $_.Status -eq "Up" }).MacAddress | Select-Object -First 1
    }

    $os = Invoke-Command -Session $session -ScriptBlock {
        (Get-CimInstance Win32_OperatingSystem).Caption
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
    Write-Output "Error: $($_.Exception.Message)"
}