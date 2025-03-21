# Script: ApagarPC.ps1
param($computer)

if (-not $computer) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

# Credenciales para el PC seleccionado
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Contraseña del administrador
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

Write-Host "Enviando comando de apagado a $computer..." -ForegroundColor Yellow
try {
    Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
        Stop-Computer -Force
    }
    Write-Host "Comando enviado. $computer debería apagarse en breve." -ForegroundColor Green
} catch {
    Write-Output "Error al apagar $computer : $_"
}