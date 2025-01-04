import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import Notification
from channels.db import database_sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Connect to the WebSocket and join the user's notification group.
        """
        request_user = self.scope['user']
        
        if request_user is not None:
            self.user_id = self.scope["user"].id
            self.group_name = f"notifications_{self.user_id}"

            # Add this channel to the group
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.accept()

            # Fetch and send old notifications
            old_notifications = await self.get_old_notifications()
            await self.send(text_data=json.dumps({
                "type": "old_notifications",
                "data": old_notifications
            }))
        else:
            # Reject the connection if the user is not authenticated
            await self.close()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_notification(self, event):
        """
        Send a new notification to the WebSocket client.
        """
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "notification": event["notification"]
        }))

    @database_sync_to_async
    def get_old_notifications(self):
        """
        Fetch old notifications for the authenticated user.
        This function is now wrapped using `sync_to_async`.
        """
        group_name = f"notifications_{self.user_id}"
        try:
            notifications = Notification.objects.filter(group_name=group_name).order_by('-created_at')
            serialized_notifications = [
                {
                    "id": notification.id ,
                    "group_name": notification.group_name,
                    "patient_message": notification.patient_message,
                    "doctor_message": notification.doctor_message,
                    "type": notification.type,
                    "is_read": notification.is_read,
                    "created_at": notification.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for notification in notifications
            ]
            return serialized_notifications
        
        except Exception as e:
            # Log the error for debugging
            print(f"Error fetching old notifications: {e}")
            return []
