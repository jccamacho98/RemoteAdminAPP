from django.urls import path
from . import views

urlpatterns = [
    path('', views.monitor, name='monitor'),
    path('api/pcs/', views.api_get_pcs, name='api_get_pcs'),
    path('api/update_info/', views.api_update_info, name='api_update_info'),
]