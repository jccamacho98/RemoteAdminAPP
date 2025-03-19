# Script: ApagarPC.ps1
$computer = "PC01"

# Credenciales para PC01 (usa las mismas que en PruebaInstalarSoftware.ps1 y PruebaDesinstalarSoftware.ps1)
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Cambia por la contraseña real de PC01
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

Write-Host "Enviando comando de apagado a $computer..." -ForegroundColor Yellow
Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
    Stop-Computer -Force
}
Write-Host "Comando enviado. $computer debería apagarse en breve." -ForegroundColor Green