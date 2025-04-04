# Script: InfoSoftwareInstalado.ps1
param (
    [Parameter(Mandatory=$true)]
    [string]$computer  # Nombre del PC remoto
)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Suprimir mensajes de progreso
$ProgressPreference = 'SilentlyContinue'

# Validar parámetros
if (-not $computer) {
    $errorMessage = @{ status = "error"; message = "No se proporcionó el nombre del PC." } | ConvertTo-Json -Compress
    Write-Output $errorMessage
    exit 1
}

# Leer credenciales desde variables de entorno
$username = $env:WINRM_USERNAME
$password = $env:WINRM_PASSWORD

# Validar que las credenciales estén definidas
if (-not $username -or -not $password) {
    $errorMessage = @{ status = "error"; message = "Las variables de entorno WINRM_USERNAME y WINRM_PASSWORD deben estar definidas." } | ConvertTo-Json -Compress
    Write-Output $errorMessage
    exit 1
}

$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Validar si el PC está en línea usando Test-Connection
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        $errorMessage = @{ status = "error"; message = "$computer no está en línea. No se puede obtener la información de software." } | ConvertTo-Json -Compress
        Write-Output $errorMessage
        exit 0
    }
}
catch {
    $errorMessage = @{ status = "error"; message = "Error al verificar la conectividad con $computer : $($_.Exception.Message)" } | ConvertTo-Json -Compress
    Write-Output $errorMessage
    exit 1
}

# Obtener software instalado usando Invoke-Command
try {
    $software = Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
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
    } -ErrorAction Stop

    if ($software) {
        $result = @{ status = "success"; data = $software } | ConvertTo-Json -Compress -Depth 4
        $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($result)
        $utf8String = [System.Text.Encoding]::UTF8.GetString($utf8Bytes)
        Write-Output $utf8String
    } else {
        $result = @{ status = "success"; data = @() } | ConvertTo-Json -Compress
        $utf8Bytes = [System.Text.Encoding]::UTF8.GetBytes($result)
        $utf8String = [System.Text.Encoding]::UTF8.GetString($utf8Bytes)
        Write-Output $utf8String
    }
}
catch {
    $errorMessage = @{ status = "error"; message = "Error al obtener la lista de software en $computer : $($_.Exception.Message)" } | ConvertTo-Json -Compress
    Write-Output $errorMessage
    exit 1
}