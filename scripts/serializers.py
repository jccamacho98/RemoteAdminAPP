from rest_framework import serializers
from monitor.models import Info_PCs

class InfoPCSerializer(serializers.ModelSerializer):
    class Meta:
        model = Info_PCs
        fields = ['nombre', 'ip', 'mac_address', 'sistema_operativo', 'estado', 'domain_joined', 'last_seen']