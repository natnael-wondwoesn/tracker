from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import status
from .models import ChatMessage
from core.models import CustomUser
from django.db.models import Q

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_messages(request, chatroom_id):
    messages = ChatMessage.objects.filter(chatroom_id=chatroom_id).order_by('timestamp')
    return Response([{
        'id': msg.id,
        'sender_id': msg.sender.id,
        'receiver_id': msg.receiver.id,
        'message': msg.message,
        'timestamp': msg.timestamp.isoformat()
    } for msg in messages])

@api_view(['GET'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def get_client_list(request):
    user_id = request.user.id
    messages = ChatMessage.objects.filter(Q(sender_id=user_id) | Q(receiver_id=user_id))
    user_ids = set(
        msg.sender_id if msg.receiver_id == user_id else msg.receiver_id
        for msg in messages
    )
    clients = CustomUser.objects.filter(id__in=user_ids)
    return Response([{
        'id': user.id,
        'username': user.username
    } for user in clients])

@api_view(['POST'])
@authentication_classes([JWTAuthentication])
@permission_classes([IsAuthenticated])
def send_message(request):
    sender_id = request.user.id
    receiver_id = request.data.get('receiver_id')
    message = request.data.get('message')
    
    if not all([receiver_id, message]):
        return Response({'error': 'Missing receiver_id or message'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        receiver = CustomUser.objects.get(id=receiver_id)
    except CustomUser.DoesNotExist:
        return Response({'error': 'Receiver not found'}, status=status.HTTP_404_NOT_FOUND)
    
    chatroom_id = f"{min(sender_id, int(receiver_id))}_{max(sender_id, int(receiver_id))}"
    
    msg = ChatMessage.objects.create(
        chatroom_id=chatroom_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        message=message
    )
    
    return Response({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'receiver_id': msg.receiver_id,
        'message': msg.message,
        'timestamp': msg.timestamp.isoformat()
    }, status=status.HTTP_201_CREATED)