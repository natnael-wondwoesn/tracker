from django.urls import path
from . import views

urlpatterns = [
    path('getMessages/<str:chatroom_id>/', views.get_messages, name='get_messages'),
    path('clients/<int:receiver_id>/', views.get_client_list, name='get_client_list'),
    path('sendMessage/', views.send_message, name='send_message'),
]