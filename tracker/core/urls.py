from django.urls import path
from .views import (
    RegisterUserView, UserDetailView, UserMeView, VerifyEmailView, LoginView, 
    LogoutView, AdminApprovalView, AdminLoginView, ChildProfileView,
    SwitchActiveChildView, UserListView
)
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('register/', RegisterUserView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify_email'),
    path('admin-login/', AdminLoginView.as_view(), name='admin_login'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('admin-approve/', AdminApprovalView.as_view(), name='admin_approval'),
    path('child-profiles/', ChildProfileView.as_view(), name='child-profile-list-create'),
    path('child-profiles/<int:child_id>/', ChildProfileView.as_view(), name='child-profile-detail'),
    path('child-profiles/<int:child_id>/switch/', SwitchActiveChildView.as_view(), name='switch-active-child'),
    path('users/', UserListView.as_view(), name='user-list'),
    path('users/<int:user_id>/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/', UserMeView.as_view(), name='user-me'),
    path('switch-active-child/<int:child_id>/', SwitchActiveChildView.as_view(), name='switch-active-child'),
]
