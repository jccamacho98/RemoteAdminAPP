$username = "SERVER331NB\administrator"
$password = "Sala331server"
$securePassword = ConvertTo-SecureString $password -AsPlainText -Force
$credential = New-Object System.Management.Automation.PSCredential ($username, $securePassword)
Enter-PSSession -ComputerName PC01 -Credential $credential