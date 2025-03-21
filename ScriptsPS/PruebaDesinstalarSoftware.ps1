# Script: PruebaDesinstalarSoftware.ps1
# Descripción: Desinstala 7-Zip de PC01 de forma remota

# Nombre del PC objetivo
$computer = "PC01"

# Ruta del ejecutable de desinstalación en PC01
$uninstallPath = "C:\Program Files\7-Zip\Uninstall.exe"

# Credenciales para PC01 (usa las mismas que en PruebaInstalarSoftware.ps1)
$username = "SERVER331NB\administrator"  # O "SERVER331.local\Administrator" si es un dominio
$password = "Sala331server"  # Cambia por la contraseña real de PC01
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

Write-Host "Conectando a $computer para desinstalar 7-Zip..." -ForegroundColor Yellow

# Verificar si el archivo de desinstalación existe y desinstalar
Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
    if (Test-Path $using:uninstallPath) {
        Write-Host "Iniciando desinstalación de 7-Zip en $env:COMPUTERNAME..." -ForegroundColor Yellow
        Start-Process -FilePath $using:uninstallPath -ArgumentList "/S" -Wait -NoNewWindow
        Write-Host "7-Zip desinstalado exitosamente en $env:COMPUTERNAME" -ForegroundColor Green
    } else {
        Write-Host "Error: No se encontró $using:uninstallPath. 7-Zip no está instalado o la ruta es incorrecta." -ForegroundColor Red
    }
}

Write-Host "Proceso de desinstalación finalizado en $computer." -ForegroundColor Green