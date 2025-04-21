param (
    [Parameter(Mandatory=$true)]
    [string]$computer
)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Suprimir mensajes de progreso
$ProgressPreference = 'SilentlyContinue'

# Leer credenciales desde variables de entorno
$username = $env:WINRM_USERNAME
$password = $env:WINRM_PASSWORD

if (-not $username -or -not $password) {
    Write-Output "Error: Las variables de entorno WINRM_USERNAME y WINRM_PASSWORD deben estar definidas."
    exit 1
}

$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Verificar si el PC está en línea con ping
$status = "Offline"
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if ($pingResult) {
        # Si el ping tiene éxito, verificar si el dispositivo es el PC correcto consultando Active Directory
        try {
            # Obtener el nombre del equipo desde Active Directory
            $adComputer = Get-ADComputer -Filter {Name -eq $computer} -Credential $credential -ErrorAction Stop
            if ($adComputer) {
                # Obtener la dirección IP del dispositivo que respondió al ping
                $ipAddress = [System.Net.Dns]::GetHostAddresses($computer) | Where-Object { $_.AddressFamily -eq 'InterNetwork' } | Select-Object -First 1
                if ($ipAddress) {
                    $ipAddress = $ipAddress.IPAddressToString
                    Write-Output "IP resuelta para ${computer}: $ipAddress"

                    # Verificar si el equipo en AD tiene esa IP (o validar de otra manera)
                    # Intentar conectarse al equipo y obtener su nombre real
                    $remoteComputerName = Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock { $env:COMPUTERNAME } -ErrorAction Stop
                    if ($remoteComputerName -eq $computer) {
                        $status = "Online"
                    } else {
                        Write-Output "El dispositivo que respondió al ping no es ${computer} (Nombre real: $remoteComputerName)"
                        $status = "Offline"
                    }
                } else {
                    Write-Output "No se pudo resolver la IP de ${computer}"
                    $status = "Offline"
                }
            } else {
                Write-Output "El equipo ${computer} no está registrado en Active Directory"
                $status = "Offline"
            }
        } catch {
            Write-Output "Error al consultar Active Directory o al conectarse a ${computer}: $($_.Exception.Message)"
            $status = "Offline"
        }
    }
} catch {
    Write-Output "Error: No se pudo verificar la conectividad con ${computer}: $($_.Exception.Message)"
    $status = "Offline"
}

# Devolver solo el estado
"Status: $status"