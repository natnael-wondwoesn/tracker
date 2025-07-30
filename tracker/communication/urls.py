from django.urls import path
from . import views

urlpatterns = [
    # Forum Categories
    path('categories/', views.ForumCategoryView.as_view(), name='forum-category-list'),
    path('categories/<int:pk>/', views.ForumCategoryDetailView.as_view(), name='forum-category-detail'),
    
    # Forum Posts
    path('posts/', views.ForumPostView.as_view(), name='forum-post-list'),
    path('posts/<uuid:pk>/', views.ForumPostDetailView.as_view(), name='forum-post-detail'),
    
    # Forum Comments
    path('posts/<uuid:post_pk>/comments/', views.ForumCommentView.as_view(), name='forum-comment-list'),
    path('posts/<uuid:post_pk>/comments/<uuid:pk>/', views.ForumCommentDetailView.as_view(), name='forum-comment-detail'),
    
    # Chat Rooms
    path('chat-rooms/', views.ChatRoomView.as_view(), name='chat-room-list'),
    path('chat-rooms/<uuid:pk>/', views.ChatRoomDetailView.as_view(), name='chat-room-detail'),
    
    # Firebase Token
    path('firebase-token/', views.FirebaseTokenView.as_view(), name='firebase-token'),
] 