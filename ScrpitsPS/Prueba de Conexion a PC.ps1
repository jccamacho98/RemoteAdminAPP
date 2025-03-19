$computer= "PC01"
Write-Host "Conectado a $computer..." -ForegroundColor Green
Invoke-Command -ComputerName $computer -ScriptBlock {
    Write-Host "Nombre del equipo: $env:COMPUTERNAME"
    Write-Host "Hora actual: $(Get-Date)"

}
Write-Host "...................."