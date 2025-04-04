from django.shortcuts import render
from monitor.models import Info_PCs 

def index(request):
    pcs = Info_PCs.objects.all().order_by('nombre')
    col1_pcs = pcs[0:5]
    col2_pcs = pcs[5:10]
    col3_pcs = pcs[10:15]
    col4_pcs = pcs[15:20]
    return render(request, 'index.html', {
        'col1_pcs': col1_pcs,
        'col2_pcs': col2_pcs,
        'col3_pcs': col3_pcs,
        'col4_pcs': col4_pcs,
        'output': None
    })