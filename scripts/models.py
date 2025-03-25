from django.db import models

class Info_PCs(models.Model):
    nombre = models.CharField(max_length=10, unique=True)  # Ejemplo: "PC01"
    ip = models.CharField(max_length=15, blank=True, null=True)  # Ejemplo: "192.168.128.11"
    mac_address = models.CharField(max_length=17, blank=True, null=True)  # Ejemplo: "00:1A:2B:3C:4D:5E"
    sistema_operativo = models.CharField(max_length=50, blank=True, null=True)  # Ejemplo: "Windows 10 Pro"
    estado = models.CharField(max_length=10, choices=[('Online', 'Online'), ('Offline', 'Offline')], default='Offline')
    domain_joined = models.BooleanField(default=False)
    last_seen = models.DateTimeField(blank=True, null=True)
    procesador = models.CharField(max_length=50,unique=False)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'Info_PCs'  # Nombre exacto de la tabla en MySQL