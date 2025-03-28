from django.shortcuts import render
from scripts.models import Info_PCs
from scripts.utils import update_pc_status, update_pc_info
from rest_framework.decorators import api_view
from rest_framework.response import Response
from scripts.serializers import InfoPCSerializer

def monitor(request):
    # Actualizar solo el estado al cargar la vista
    if request.method != "POST":
        update_pc_status()
    
    pcs = Info_PCs.objects.all().order_by('nombre')
    output = None
    if request.method == "POST" and 'update_info' in request.POST:
        # Ejecutar la actualización de forma síncrona
        output = update_pc_info()
    return render(request, 'monitor/monitor.html', {'pcs': pcs, 'output': output})

@api_view(['GET'])
def api_get_pcs(request):
    pcs = Info_PCs.objects.all().order_by('nombre')
    serializer = InfoPCSerializer(pcs, many=True)
    return Response(serializer.data)

@api_view(['POST'])
def api_update_info(request):
    output = update_pc_info()
    return Response({'message': 'Actualización completada.', 'output': output})