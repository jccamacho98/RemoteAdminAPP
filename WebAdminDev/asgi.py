"""
ASGI config for WebAdminDev project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import monitor.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'WebAdminDev.settings')

application = ProtocolTypeRouter({
    'http': get_asgi_application(),  # Maneja solicitudes HTTP (Django estándar)
    'websocket': AuthMiddlewareStack(  # Maneja WebSockets
        URLRouter(
            monitor.routing.websocket_urlpatterns
        )
    ),
})