# Script: ConectarRDP_PC01.ps1
$computer = "PC01"

Write-Host "Iniciando conexión RDP a $computer..." -ForegroundColor Yellow

# Iniciar sesión RDP sin pasar credenciales automáticamente
Start-Process -FilePath "mstsc.exe" -ArgumentList "/v:$computer"

Write-Host "Conexión RDP iniciada. Introduce las credenciales manualmente (SERVER331NB\administrator, Sala331server)." -ForegroundColor Green