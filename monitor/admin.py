from django.contrib import admin
from monitor.models import Info_PCs, SoftwareInstalado

@admin.register(Info_PCs)
class InfoPCsAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ip', 'mac_address', 'sistema_operativo', 'estado', 'domain_joined', 'last_seen', 'procesador')
    list_filter = ('estado', 'domain_joined')
    search_fields = ('nombre', 'ip', 'procesador')

@admin.register(SoftwareInstalado)
class SoftwareInstaladoAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'pc', 'display_version', 'publisher', 'install_date', 'last_updated')
    list_filter = ('pc', 'last_updated')
    search_fields = ('display_name', 'publisher')