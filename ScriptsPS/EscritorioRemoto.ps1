$computer = "PC01"
$rdpFilePath = "C:\WebAdminDev\ScriptsPS\PC01.rdp"

# Verificar si el archivo .rdp existe
if (Test-Path $rdpFilePath) {
    # Forzar la salida en UTF-8
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    Write-Output "Haz clic en el enlace para iniciar la conexión a ${computer}: file://C:/WebAdminDev/ScriptsPS/PC01.rdp"
} else {
    Write-Output "Error: El archivo RDP no existe en $rdpFilePath. Por favor, genera el archivo primero."
}