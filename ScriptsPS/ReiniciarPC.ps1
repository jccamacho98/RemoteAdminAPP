# Script: ApagarPC.ps1
param($computer)

if (-not $computer) {
    Write-Output "Error: No se proporcionó el nombre del PC."
    exit 1
}

$username = "SERVER331NB\administrator"
$password = "Sala331server"
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

Write-Host "Enviando comando de reinicio a $computer..." -ForegroundColor Yellow
Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
    Restart-Computer -Force
}
Write-Host "Comando enviado. $computer debería reiniciarse en breve." -ForegroundColor Green