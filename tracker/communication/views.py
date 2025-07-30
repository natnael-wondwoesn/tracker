from django.shortcuts import render, get_object_or_404
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import ForumCategory, ForumPost, ForumComment, ChatRoom, FirebaseToken
from .serializers import (
    ForumCategorySerializer, ForumPostSerializer, ForumCommentSerializer,
    ChatRoomSerializer, FirebaseTokenSerializer
)
from core.models import CustomUser, ChildProfile
import logging

logger = logging.getLogger(__name__)

class ForumCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = ForumCategory.objects.all()
        serializer = ForumCategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ForumCategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForumCategoryDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ForumCategory, pk=pk)

    def get(self, request, pk):
        category = self.get_object(pk)
        serializer = ForumCategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk)
        serializer = ForumCategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ForumPostView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        posts = ForumPost.objects.all().select_related('author', 'category')
        serializer = ForumPostSerializer(posts, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request):
        serializer = ForumPostSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForumPostDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ForumPost, pk=pk)

    def get(self, request, pk):
        post = self.get_object(pk)
        serializer = ForumPostSerializer(post, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        post = self.get_object(pk)
        if post.author != request.user:
            return Response(
                {'error': 'Only the author can update this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ForumPostSerializer(post, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        post = self.get_object(pk)
        if post.author != request.user:
            return Response(
                {'error': 'Only the author can delete this post'},
                status=status.HTTP_403_FORBIDDEN
            )
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, pk):
        post = self.get_object(pk)
        action = request.data.get('action')
        
        if action == 'like':
            if request.user in post.likes.all():
                post.likes.remove(request.user)
                return Response({'status': 'unliked'})
            else:
                post.likes.add(request.user)
                return Response({'status': 'liked'})
        elif action == 'toggle_anonymous':
            if post.author != request.user:
                return Response(
                    {'error': 'Only the author can toggle anonymous status'},
                    status=status.HTTP_403_FORBIDDEN
                )
            post.is_anonymous = not post.is_anonymous
            post.save()
            return Response({'is_anonymous': post.is_anonymous})
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ForumCommentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, post_pk):
        comments = ForumComment.objects.filter(post_id=post_pk).select_related('author')
        serializer = ForumCommentSerializer(comments, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, post_pk):
        post = get_object_or_404(ForumPost, pk=post_pk)
        serializer = ForumCommentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(author=request.user, post=post)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ForumCommentDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, post_pk, pk):
        return get_object_or_404(ForumComment, post_id=post_pk, pk=pk)

    def get(self, request, post_pk, pk):
        comment = self.get_object(post_pk, pk)
        serializer = ForumCommentSerializer(comment, context={'request': request})
        return Response(serializer.data)

    def put(self, request, post_pk, pk):
        comment = self.get_object(post_pk, pk)
        if comment.author != request.user:
            return Response(
                {'error': 'Only the author can update this comment'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ForumCommentSerializer(comment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, post_pk, pk):
        comment = self.get_object(post_pk, pk)
        if comment.author != request.user:
            return Response(
                {'error': 'Only the author can delete this comment'},
                status=status.HTTP_403_FORBIDDEN
            )
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def post(self, request, post_pk, pk):
        comment = self.get_object(post_pk, pk)
        action = request.data.get('action')
        
        if action == 'like':
            if request.user in comment.likes.all():
                comment.likes.remove(request.user)
                return Response({'status': 'unliked'})
            else:
                comment.likes.add(request.user)
                return Response({'status': 'liked'})
        elif action == 'toggle_anonymous':
            if comment.author != request.user:
                return Response(
                    {'error': 'Only the author can toggle anonymous status'},
                    status=status.HTTP_403_FORBIDDEN
                )
            comment.is_anonymous = not comment.is_anonymous
            comment.save()
            return Response({'is_anonymous': comment.is_anonymous})
        
        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )

class ChatRoomView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role == 'parent':
            chat_rooms = ChatRoom.objects.filter(parent=user).select_related('therapist', 'child')
        elif user.role == 'therapist':
            chat_rooms = ChatRoom.objects.filter(therapist=user).select_related('parent', 'child')
        else:
            chat_rooms = ChatRoom.objects.none()
        
        serializer = ChatRoomSerializer(chat_rooms, many=True)
        return Response(serializer.data)

    def post(self, request):
        therapist_id = request.data.get('therapist_id')
        child_id = request.data.get('child_id')

        try:
            therapist = CustomUser.objects.get(id=therapist_id, role='therapist')
            child = ChildProfile.objects.get(id=child_id, parent=request.user)
        except (CustomUser.DoesNotExist, ChildProfile.DoesNotExist):
            return Response(
                {'error': 'Invalid therapist or child ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        chat_room, created = ChatRoom.objects.get_or_create(
            parent=request.user,
            therapist=therapist,
            child=child
        )

        serializer = ChatRoomSerializer(chat_room)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class ChatRoomDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(ChatRoom, pk=pk)

    def get(self, request, pk):
        chat_room = self.get_object(pk)
        if request.user not in [chat_room.parent, chat_room.therapist]:
            return Response(
                {'error': 'You do not have permission to view this chat room'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = ChatRoomSerializer(chat_room)
        return Response(serializer.data)

    def delete(self, request, pk):
        chat_room = self.get_object(pk)
        if request.user != chat_room.parent:
            return Response(
                {'error': 'Only the parent can delete this chat room'},
                status=status.HTTP_403_FORBIDDEN
            )
        chat_room.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class FirebaseTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = FirebaseTokenSerializer(data=request.data)
        if serializer.is_valid():
            token, created = FirebaseToken.objects.update_or_create(
                user=request.user,
                defaults={
                    'token': serializer.validated_data['token'],
                    'device_id': serializer.validated_data['device_id']
                }
            )
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
