import winrm

session = winrm.Session('http://localhost:5985/wsman', auth=('SERVER331NB\\Administrator', 'Sala331server'))
result = session.run_ps('powershell -File "D:\\ScriptsPS\\PruebaInstalarSoftware.ps1"')
print(result.std_out.decode('utf-8'))
print(result.std_err.decode('utf-8'))