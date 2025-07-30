from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from pusher import Pusher
from .models import Conversation
from core.models import CustomUser

# Instantiate Pusher
pusher = Pusher(
    app_id='1998207',
    key='2f35b2d1c52c01e9f37b',
    secret='01a2e1a817a771f6e49f',
    cluster='mt1'
)

# Render chat page
@login_required(login_url='login/')
def index(request):
    return render(request, "chat.html")

# Broadcast message via Pusher
class BroadcastView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        message_text = request.data.get('message', '')
        if not message_text:
            return Response({'error': 'Message is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Save message to database
        message = Conversation(message=message_text, status='', user=request.user)
        message.save()
        
        # Prepare message data for Pusher
        message_data = {
            'name': message.user.first_name,
            'status': message.status,
            'message': message.message,
            'id': message.id
        }
        
        # Trigger Pusher event
        pusher.trigger('a_channel', 'an_event', message_data)
        
        return Response(message_data, status=status.HTTP_201_CREATED)

# Fetch all conversations
class ConversationsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.all()
        data = [
            {
                'name': conv.user.first_name,
                'status': conv.status,
                'message': conv.message,
                'id': conv.id
            }
            for conv in conversations
        ]
        return Response(data, status=status.HTTP_200_OK)

# Update message delivery status
class DeliveredView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            message = Conversation.objects.get(pk=id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.user.id == message.user.id:
            return Response({'status': 'Awaiting Delivery'}, status=status.HTTP_400_BAD_REQUEST)
        
        socket_id = request.data.get('socket_id', '')
        message.status = 'Delivered'
        message.save()
        
        message_data = {
            'name': message.user.first_name,
            'status': message.status,
            'message': message.message,
            'id': message.id
        }
        
        pusher.trigger('a_channel', 'delivered_message', message_data, socket_id)
        
        return Response({'status': 'ok'}, status=status.HTTP_200_OK)