# Script: PruebaInstalarSoftware.ps1
param (
    [string]$computer,           # Nombre del PC donde se instalará el software
    [string]$installerPath,      # Ruta del instalador en el servidor (proporcionada por el usuario)
    [string]$remoteDestination,  # Ruta de destino en el PC remoto (por ejemplo, C:\Software\installer.exe)
    [switch]$unattended          # Indicador para instalación desatendida (silenciosa)
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

if (-not $installerPath) {
    Write-Output "Error: No se proporcionó la ruta del instalador."
    exit 1
}

if (-not $remoteDestination) {
    Write-Output "Error: No se proporcionó la ruta de destino en el PC remoto."
    exit 1
}

# Credenciales para el PC seleccionado
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Contraseña del administrador
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Validar si el PC está en línea usando Test-Connection
Write-Output "Verificando si $computer está en línea..."
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        Write-Output "$computer no está en línea. No se intentará instalar el software."
        exit 0  # Salir con código 0 (éxito, pero no se instaló porque no está en línea)
    }
    Write-Output "$computer está en línea. Procediendo con la instalación..."
}
catch {
    Write-Output "Error al verificar la conectividad con $computer : $($_.Exception.Message)"
    exit 1  # Salir con código 1 (error)
}

# Validar si el instalador existe en el servidor
if (-not (Test-Path $installerPath)) {
    Write-Output "Error: No se encontró el instalador en $installerPath."
    exit 1
}

# Crear la carpeta de destino en el PC remoto si no existe
$remoteDir = [System.IO.Path]::GetDirectoryName($remoteDestination)
Write-Output "Verificando si la carpeta $remoteDir existe en $computer..."
try {
    $session = New-PSSession -ComputerName $computer -Credential $credential -ErrorAction Stop
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

# Verificar si el instalador ya existe en el PC remoto
Write-Output "Verificando si el instalador ya existe en $remoteDestination en $computer..."
$installerExists = $false
try {
    $installerExists = Invoke-Command -Session $session -ScriptBlock {
        param($dest)
        Test-Path $dest
    } -ArgumentList $remoteDestination -ErrorAction Stop
}
catch {
    Write-Output "Error al verificar la existencia del instalador en $computer : $($_.Exception.Message)"
    Remove-PSSession $session -ErrorAction SilentlyContinue
    exit 1
}

# Copiar el instalador al PC remoto solo si no existe
if (-not $installerExists) {
    Write-Output "Copiando instalador a $computer en $remoteDestination..."
    try {
        Copy-Item -Path $installerPath -Destination $remoteDestination -ToSession $session -Force -ErrorAction Stop
        Write-Output "Instalador copiado exitosamente a $remoteDestination en $computer."
    }
    catch {
        Write-Output "Error al copiar el instalador a $computer : $($_.Exception.Message)"
        Remove-PSSession $session -ErrorAction SilentlyContinue
        exit 1
    }
} else {
    Write-Output "El instalador ya existe en $remoteDestination en $computer. No se realizó la copia."
}

# Instalar el software en el PC remoto
Write-Output "Instalando software en $computer..."
try {
    if ($unattended) {
        # Instalación desatendida: ejecutar directamente con Start-Process y esperar a que termine
        Invoke-Command -Session $session -ScriptBlock {
            param($installer)
            Start-Process -FilePath $installer -ArgumentList "/S" -Wait -NoNewWindow -ErrorAction Stop
            Write-Output "Instalación desatendida completada en $env:COMPUTERNAME."
        } -ArgumentList $remoteDestination -ErrorAction Stop
        Write-Output "Éxito: Software instalado en $computer."
    } else {
        # Instalación atendida: no ejecutar el instalador, solo informar al usuario
        Write-Output "Advertencia: Has seleccionado instalación atendida (interactiva)."
        Write-Output "Para continuar con la instalación, debes iniciar una sesión de Escritorio Remoto en $computer."
        Write-Output "El instalador está listo en $remoteDestination y debe ejecutarse manualmente."
    }
}
catch {
    Write-Output "Error al instalar el software en $computer : $($_.Exception.Message)"
    Remove-PSSession $session -ErrorAction SilentlyContinue
    exit 1
}

# Cerrar la sesión
Remove-PSSession $session
Write-Output "Proceso finalizado."