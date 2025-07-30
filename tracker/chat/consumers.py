import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import ChatMessage
from core.models import CustomUser
from channels.db import database_sync_to_async
from channels.auth import AuthMiddlewareStack

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sender_id = self.scope['user'].id or 2  # Match token user_id
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']
        self.chatroom_id = f"{min(int(self.sender_id), int(self.receiver_id))}_{max(int(self.sender_id), int(self.receiver_id))}"
        self.room_group_name = f"chat_{self.chatroom_id}"
        print(f"Connecting to chatroom: {self.room_group_name}")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        sender_id = self.scope['user'].id or 2
        receiver_id = self.receiver_id
        print(f"Received message: {message} from {sender_id}")
        await self.save_message(sender_id, receiver_id, message, self.chatroom_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat.message',
                'message': message,
                'sender_id': sender_id,
                'timestamp': str(ChatMessage.objects.latest('timestamp').timestamp)
            }
        )

    async def chat_message(self, event):
        print(f"Sending message to client: {event['message']}")
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, message, chatroom_id):
        ChatMessage.objects.create(
            chatroom_id=chatroom_id,
            sender_id=sender_id,
            receiver_id=receiver_id,
            message=message
        )