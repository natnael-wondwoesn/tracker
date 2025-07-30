from django.contrib import admin
from .models import ForumCategory, ForumPost, ForumComment, ChatRoom, FirebaseToken

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)

@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_anonymous', 'created_at', 'updated_at')
    list_filter = ('category', 'is_anonymous', 'created_at', 'updated_at')
    search_fields = ('title', 'content', 'author__email')
    raw_id_fields = ('author', 'category', 'likes')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'is_anonymous', 'created_at', 'updated_at')
    list_filter = ('is_anonymous', 'created_at', 'updated_at')
    search_fields = ('content', 'author__email', 'post__title')
    raw_id_fields = ('post', 'author', 'likes')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('parent', 'therapist', 'child', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('parent__email', 'therapist__email', 'child__first_name', 'child__last_name')
    raw_id_fields = ('parent', 'therapist', 'child')
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')

@admin.register(FirebaseToken)
class FirebaseTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'device_id', 'created_at', 'updated_at')
    search_fields = ('user__email', 'device_id')
    raw_id_fields = ('user',)
    ordering = ('-updated_at',)
    readonly_fields = ('created_at', 'updated_at')
