from rest_framework import serializers
from .models import ForumCategory, ForumPost, ForumComment, ChatRoom, FirebaseToken
from core.models import CustomUser

class ForumCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ForumCategory
        fields = ['id', 'name', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role']

class ForumPostSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = ForumPost
        fields = [
            'id', 'author', 'category', 'title', 'content', 
            'created_at', 'updated_at', 'is_anonymous',
            'likes_count', 'comments_count', 'is_liked'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_comments_count(self, obj):
        return obj.comments.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class ForumCommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = ForumComment
        fields = [
            'id', 'post', 'author', 'content', 
            'created_at', 'updated_at', 'is_anonymous',
            'likes_count', 'is_liked'
        ]
        read_only_fields = ['author', 'created_at', 'updated_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(id=request.user.id).exists()
        return False

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)

class ChatRoomSerializer(serializers.ModelSerializer):
    parent = UserSerializer(read_only=True)
    therapist = UserSerializer(read_only=True)
    child_name = serializers.CharField(source='child.full_name', read_only=True)

    class Meta:
        model = ChatRoom
        fields = [
            'id', 'parent', 'therapist', 'child', 'child_name',
            'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['created_at', 'updated_at']

class FirebaseTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = FirebaseToken
        fields = ['token', 'device_id']
        extra_kwargs = {
            'token': {'required': True},
            'device_id': {'required': True}
        } 