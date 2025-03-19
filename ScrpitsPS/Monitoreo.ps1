# Script: MonitorearPC01.ps1
$computer = "PC01"

# Credenciales para PC01
$username = "SERVER331NB\administrator"
$password = "Sala331server"
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)

Write-Host "Monitoreando $computer..." -ForegroundColor Yellow
Invoke-Command -ComputerName $computer -Credential $credential -ScriptBlock {
    # Uso de CPU con CIM
    $cpu = Get-CimInstance Win32_PerfFormattedData_PerfOS_Processor | Where-Object { $_.Name -eq "_Total" }
    $cpuPercent = [math]::Round($cpu.PercentProcessorTime, 2)

    # Memoria disponible con CIM
    $os = Get-CimInstance Win32_OperatingSystem
    $memoryFreeMB = [math]::Round($os.FreePhysicalMemory / 1024, 2)  # KB a MB
    $memoryTotalMB = [math]::Round($os.TotalVisibleMemorySize / 1024, 2)

    # Espacio en disco C:
    $disk = Get-Disk | Get-Partition | Get-Volume | Where-Object { $_.DriveLetter -eq "C" }
    $freeSpaceGB = [math]::Round($disk.SizeRemaining / 1GB, 2)
    $totalSpaceGB = [math]::Round($disk.Size / 1GB, 2)

    # Procesos en ejecución
    $processCount = (Get-Process).Count

    Write-Host "Uso de CPU: $cpuPercent %" -ForegroundColor Cyan
    Write-Host "Memoria disponible: $memoryFreeMB MB de $memoryTotalMB MB" -ForegroundColor Cyan
    Write-Host "Espacio libre en C: $freeSpaceGB GB de $totalSpaceGB GB" -ForegroundColor Cyan
    Write-Host "Procesos en ejecución: $processCount" -ForegroundColor Cyan
}
Write-Host "Monitoreo completo." -ForegroundColor Green