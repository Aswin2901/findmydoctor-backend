import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from rest_framework_simplejwt.tokens import AccessToken
from doctors.models import Doctor
from accounts.tokenauthentication import JWTAuthentication
from chat.models import ChatMessage


class PersonalChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """
        Handle the WebSocket connection.
        Authenticate the user and set up the chat room.
        """
        request_user = self.scope['user']
        print("Authenticated user:", request_user)

        # If the user is authenticated and the role is 'doctor', manually handle the token
        if request_user is not None:
            # Check if the user is a doctor
            if hasattr(request_user, 'is_authenticated'):
                # Extract the chat ID from URL params (ID of the user to chat with)
                chat_with_user = self.scope['url_route']['kwargs']['id']

                try:
                    # Generate a room name using sorted user IDs
                    user_ids = [int(request_user.id), int(chat_with_user)]
                    user_ids = sorted(user_ids)
                    self.room_group_name = f"chat_{user_ids[0]}-{user_ids[1]}"

                    # Add the current channel to the group
                    await self.channel_layer.group_add(self.room_group_name, self.channel_name)

                    # Accept the WebSocket connection
                    await self.accept()

                    print(f"User {request_user.id} connected to chat room {self.room_group_name}")

                    # Fetch chat history for the room
                    chat_history = await self.get_chat_history(self.room_group_name)
                    await self.send(text_data=json.dumps({
                        "type": "chat_history",
                        "messages": chat_history
                    }))
                except Exception as e:
                    print(f"Error during connection: {e}")
                    await self.close()
            else:
                # For other types of users (like doctors), you can directly handle their authentication logic
                try:
                    
                    query_string = self.scope.get("query_string", b"").decode("utf-8")

                    query_parameters = dict(
                        qp.split("=", 1) if "=" in qp else (qp, None) for qp in query_string.split("&")
                    )
                    # Extract token from the query string
                    token = query_parameters.get("token", None)

                    validated_token = AccessToken(token)

                    # Extract the doctor ID from the token
                    doctor_id = validated_token.get("user_id")
                    user = await sync_to_async(Doctor.objects.get)(id=doctor_id)

                    if user:
                        # Set the doctor as the user for the scope
                        self.scope['user'] = user

                        # Get the ID of the user to chat with
                        chat_with_user = self.scope['url_route']['kwargs']['id']
                        user_ids = [int(user.id), int(chat_with_user)]
                        user_ids = sorted(user_ids)
                        self.room_group_name = f"chat_{user_ids[0]}-{user_ids[1]}"

                        # Add the current channel to the group
                        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

                        # Accept the WebSocket connection
                        await self.accept()

                        print(f"Doctor {user.id} connected to chat room {self.room_group_name}")

                        # Fetch chat history for the room
                        chat_history = await self.get_chat_history(self.room_group_name)
                        await self.send(text_data=json.dumps({
                            "type": "chat_history",
                            "messages": chat_history
                        }))
                except Exception as e:
                    print(f"Error during doctor authentication: {e}")
                    await self.close()

        else:
            # Close the connection if the user is not authenticated
            await self.close()

    async def disconnect(self, code):
        """
        Handle the WebSocket disconnection.
        Remove the channel from the chat room group if applicable.
        """
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            print(f"Disconnected from chat room {self.room_group_name}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Handle incoming messages from the WebSocket client.
        Broadcast the message to the chat room.
        """
        if text_data:
            data = json.loads(text_data)
            message = data.get("message", "")
            sender = data.get('sender', "")

            if message:
                # Save the message in the database
                await self.save_message(self.room_group_name, message, sender)

                # Broadcast the message to the group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        "type": "chat_message",
                        "message": message,
                        "sender_id": self.scope['user'].id,
                        "sender": sender,
                    }
                )

    async def chat_message(self, event):
        """
        Receive a message from the chat room group and send it to the WebSocket client.
        """
        message = event["message"]
        sender_id = event["sender_id"]
        sender = event['sender']

        # Send the message back to the WebSocket client
        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message,
            "sender_id": sender_id,
            "sender": sender,
        }))

    @sync_to_async
    def save_message(self, group_name, message, sender):
        """
        Save a message to the database.
        """
        print(f"Saving message from {sender} in room {group_name}")
        ChatMessage.objects.create(
            group_name=group_name,
            message=message,
            sender=sender,
        )

    @sync_to_async
    def get_chat_history(self, group_name):
        """
        Fetch chat history for a specific group.
        """
        messages = ChatMessage.objects.filter(group_name=group_name).order_by('timestamp')
        return [
            {
                "message": msg.message,
                "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                "sender": msg.sender,
            }
            for msg in messages
        ]
