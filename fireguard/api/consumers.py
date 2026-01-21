import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import FireAlert

class FireAlertConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("fire_alerts", self.channel_name)
        await self.accept()
        await self.send_current_alerts()
        print("🔥 WEBSOCKET CONNECTED!")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("fire_alerts", self.channel_name)

    async def fire_alert_received(self, event):
        await self.send(text_data=json.dumps({
            'type': 'new_alert',
            'alert': event['alert']
        }))

    @database_sync_to_async
    def get_current_alerts(self):
        alerts = FireAlert.objects.order_by('-created_at')[:10]
        return [{
            'id': alert.id,
            'location_name': alert.location_name,
            'latitude': float(alert.latitude),
            'longitude': float(alert.longitude),
            'fire_size': alert.fire_size,
            'flicker_confidence': float(alert.flicker_confidence),
            'created_at': alert.created_at.isoformat()
        } for alert in alerts]

    async def send_current_alerts(self):
        alerts = await self.get_current_alerts()
        await self.send(text_data=json.dumps({
            'type': 'initial_alerts',
            'alerts': alerts
        }))