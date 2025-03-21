$computer = "PC01"
$username = "SERVER331NB\administrator"
$password = "Sala331server"

Write-Host "Generando archivo RDP para $computer..." -ForegroundColor Yellow

# Generar el contenido del archivo .rdp
$rdpContent = @"
full address:s:$computer
username:s:$username
prompt for credentials:i:1
"@
# Guardar el archivo .rdp en una ubicación accesible
$rdpFilePath = "C:\WebAdminDev\ScriptsPS\PC01.rdp"
$rdpContent | Out-File -FilePath $rdpFilePath -Encoding ASCII

Write-Host "Archivo RDP generado en: $rdpFilePath" -ForegroundColor Green
Write-Output "Archivo RDP generado. Haz clic en el enlace para iniciar la conexión a $ computer: file://C:/WebAdminDev/ScriptsPS/PC01.rdp"