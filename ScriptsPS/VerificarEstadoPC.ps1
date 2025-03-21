$computers = @("PC01", "PC02", "PC03", "PC04", "PC05", "PC06", "PC07", "PC08", "PC09", "PC10",
               "PC11", "PC12", "PC13", "PC14", "PC15", "PC16", "PC17", "PC18", "PC19", "PC20")

# Crear trabajos para verificar el estado de cada PC en paralelo
$jobs = @()
foreach ($computer in $computers) {
    $jobs += Start-Job -ScriptBlock {
        param($comp)
        try {
            $online = Test-Connection -ComputerName $comp -Count 1 -Quiet -ErrorAction Stop
            if ($online) {
                Write-Output "$comp,En línea"
            } else {
                Write-Output "$comp,Fuera de línea"
            }
        } catch {
            Write-Output "$comp,Fuera de línea"
        }
    } -ArgumentList $computer
}

# Esperar a que todos los trabajos terminen y recopilar los resultados
$results = $jobs | Wait-Job | Receive-Job
$results | ForEach-Object { Write-Output $_ }

# Limpiar los trabajos
$jobs | Remove-Job