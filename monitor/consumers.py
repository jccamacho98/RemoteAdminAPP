from channels.generic.websocket import AsyncWebsocketConsumer
import json

class PCStatusConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Agregar el cliente al grupo 'pc_status'
        await self.channel_layer.group_add('pc_status', self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Quitar el cliente del grupo al desconectarse
        await self.channel_layer.group_discard('pc_status', self.channel_name)

    # Recibir y enviar mensajes al cliente
    async def pc_status_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'pc_status_update',
            'pcs': event['pcs'],
        }))

    async def warning_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'warning_update',
            'warning': event['warning'],
        }))