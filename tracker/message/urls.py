from django.urls import path
from . import views

app_name = 'message'

urlpatterns = [
    
    path('broadcast/', views.BroadcastView.as_view(), name='broadcast'),
    path('conversations/', views.ConversationsView.as_view(), name='conversations'),
    path('delivered/<int:id>/', views.DeliveredView.as_view(), name='delivered'),
]