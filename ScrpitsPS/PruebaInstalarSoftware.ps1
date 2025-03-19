# Script: PruebaInstalarSoftware.ps1
$computer = "PC01"
$installerPath = "D:\Software\7z2409-x64.exe"
$remoteDestination = "C:\Software\7z2409-x64.exe"

# Credenciales para PC01 (ajusta según tu entorno)
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Cambia por la contraseña real de PC01
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

if (-not (Test-Path $installerPath)) {
    Write-Host "Error: No se encontró $installerPath." -ForegroundColor Red
    exit
}

Write-Host "Copiando instalador a $computer..." -ForegroundColor Yellow
$session = New-PSSession -ComputerName $computer -Credential $credential
Copy-Item -Path $installerPath -Destination $remoteDestination -ToSession $session -Force
Remove-PSSession $session

Write-Host "Instalando 7-Zip en $computer..." -ForegroundColor Green
Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
    Start-Process -FilePath "C:\Software\7z2409-x64.exe" -ArgumentList "/S" -Wait -NoNewWindow
    Write-Host "Instalación completada en $env:COMPUTERNAME" -ForegroundColor Green
}

Write-Host "Proceso finalizado." -ForegroundColor Green