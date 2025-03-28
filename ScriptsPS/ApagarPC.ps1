# Script: ApagarPC.ps1
param($computer)

# Forzar la codificación de salida a UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$PSDefaultParameterValues['Write-Output:Encoding'] = 'utf8'

# Validar si se proporcionó el nombre del PC
if (-not $computer) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

# Credenciales para el PC seleccionado
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Contraseña del administrador
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

# Validar si el PC está en línea
Write-Host "Verificando si $computer está en línea..." -ForegroundColor Yellow
try {
    $pingResult = Test-Connection -ComputerName $computer -Count 1 -Quiet -ErrorAction Stop
    if (-not $pingResult) {
        Write-Output "$computer no está en línea. No se intentará apagar."
        exit 0  # Salir con código 0 (éxito, pero no se apagó porque no está en línea)
    }
    Write-Output "$computer está en línea. Procediendo con el apagado..."
} catch {
    Write-Output "Error al verificar la conectividad con $computer : $_"
    exit 1  # Salir con código 1 (error)
}

# Enviar el comando de apagado
Write-Output "Enviando comando de apagado a $computer..."
try {
    Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
        Stop-Computer -Force
    } -ErrorAction Stop
    Write-Output "Éxito: Comando enviado. $computer debería apagarse en breve."
} catch {
    Write-Output "Error al apagar $computer : $_"
    exit 1  # Salir con código 1 (error)
}