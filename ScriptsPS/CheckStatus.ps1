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

# Verificar si el PC está en línea
$status = "Offline"
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if ($pingResult) {
        $status = "Online"
    }
}
catch {
    Write-Output "Error: No se pudo verificar la conectividad con $computer : $($_.Exception.Message)"
    exit 1
}

# Devolver solo el estado
"Status: $status"