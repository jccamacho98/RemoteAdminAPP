# Script: CopyFileToPC.ps1
param (
    [Parameter(Mandatory=$true)]
    [string]$computer,
    [Parameter(Mandatory=$true)]
    [string]$sourcePath,
    [Parameter(Mandatory=$true)]
    [string]$remoteDestination
)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Suprimir mensajes de progreso
$ProgressPreference = 'SilentlyContinue'

# Depuración: Mostrar los parámetros recibidos
Write-Output "Parámetros recibidos:"
Write-Output "  computer: $computer"
Write-Output "  sourcePath: $sourcePath"
Write-Output "  remoteDestination: $remoteDestination"

# Validar parámetros
if (-not $computer) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

if (-not $sourcePath) {
    Write-Output "Error: No se proporcionó la ruta del archivo fuente."
    exit 1
}

if (-not $remoteDestination) {
    Write-Output "Error: No se proporcionó la ruta de destino en el PC remoto."
    exit 1
}

# Credenciales codificadas directamente (como en PruebaInstalarSoftware.ps1)
$username = "SERVER331NB\administrator"  # Ajusta según tu dominio o máquina
$password = "Sala331server"              # Ajusta según tu contraseña
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Validar si el PC está en línea
Write-Output "Verificando si $computer está en línea..."
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        Write-Output "$computer no está en línea. No se intentará copiar el archivo."
        exit 0
    }
    Write-Output "$computer está en línea. Procediendo con la copia..."
}
catch {
    Write-Output "Error al verificar la conectividad con $computer : $($_.Exception.Message)"
    exit 1
}

# Validar si el archivo fuente existe en el servidor
if (-not (Test-Path $sourcePath)) {
    Write-Output "Error: El archivo fuente $sourcePath no existe en el servidor."
    exit 1
}

# Crear la sesión WinRM
try {
    $session = New-PSSession -ComputerName $computer -Credential $credential -ErrorAction Stop
}
catch {
    Write-Output "Error al crear la sesión WinRM con $computer : $($_.Exception.Message)"
    exit 1
}

# Crear la carpeta de destino en el PC remoto si no existe
$remoteDir = [System.IO.Path]::GetDirectoryName($remoteDestination)
Write-Output "Verificando si la carpeta $remoteDir existe en $computer..."
try {
    Invoke-Command -Session $session -ScriptBlock {
        param($dir)
        if (-not (Test-Path $dir)) {
            New-Item -Path $dir -ItemType Directory -Force | Out-Null
            Write-Output "Carpeta $dir creada en $env:COMPUTERNAME."
        } else {
            Write-Output "Carpeta $dir ya existe en $env:COMPUTERNAME."
        }
    } -ArgumentList $remoteDir -ErrorAction Stop
}
catch {
    Write-Output "Error al crear la carpeta $remoteDir en $computer : $($_.Exception.Message)"
    Remove-PSSession $session -ErrorAction SilentlyContinue
    exit 1
}

# Verificar si el archivo ya existe en el PC remoto
Write-Output "Verificando si el archivo ya existe en $remoteDestination en $computer..."
try {
    $fileExists = Invoke-Command -Session $session -ScriptBlock {
        param($dest)
        Test-Path $dest
    } -ArgumentList $remoteDestination -ErrorAction Stop

    if ($fileExists) {
        Write-Output "Error: El archivo ya existe en $remoteDestination en $computer."
        Remove-PSSession $session -ErrorAction SilentlyContinue
        exit 1
    }
}
catch {
    Write-Output "Error al verificar la existencia del archivo en $computer : $($_.Exception.Message)"
    Remove-PSSession $session -ErrorAction SilentlyContinue
    exit 1
}

# Copiar el archivo al PC remoto
Write-Output "Copiando archivo a $computer en $remoteDestination..."
try {
    Copy-Item -Path $sourcePath -Destination $remoteDestination -ToSession $session -Force -ErrorAction Stop
    Write-Output "Archivo copiado exitosamente a $remoteDestination en $computer."
}
catch {
    Write-Output "Error al copiar el archivo a $computer : $($_.Exception.Message)"
    Remove-PSSession $session -ErrorAction SilentlyContinue
    exit 1
}

# Cerrar la sesión
Remove-PSSession $session
Write-Output "Proceso finalizado."