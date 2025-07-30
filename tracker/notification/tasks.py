# # notification/models.py
# from django.db import models
# from django.contrib.auth.models import User
# from django.utils import timezone

# class Device(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
#     fcm_token = models.CharField(max_length=200, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         verbose_name = 'Device'
#         verbose_name_plural = 'Devices'

#     def __str__(self):
#         return f"{self.user.username}'s device"

# class NotificationLog(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     title = models.CharField(max_length=100)
#     body = models.TextField()
#     sent_at = models.DateTimeField(auto_now_add=True)
#     type = models.CharField(max_length=20, choices=[
#         ('REMINDER', 'Reminder'),
#         ('WARNING', 'Warning')
#     ])
#     success = models.BooleanField(default=False)
#     error_message = models.TextField(blank=True, null=True)

#     class Meta:
#         verbose_name = 'Notification Log'
#         verbose_name_plural = 'Notification Logs'

#     def __str__(self):
#         return f"{self.type} for {self.user.username} at {self.sent_at}"

# # notification/utils.py
# from fcm_django.models import FCMDevice
# from firebase_admin import messaging
# import firebase_admin
# from django.conf import settings
# from django.utils import timezone
# from .models import NotificationLog

# def initialize_firebase():
#     if not firebase_admin._apps:
#         cred = firebase_admin.credentials.Certificate(settings.FIREBASE_CREDENTIALS)
#         firebase_admin.initialize_app(cred)

# def send_push_notification(user, title, body, notification_type):
#     initialize_firebase()
#     devices = Device.objects.filter(user=user)
    
#     for device in devices:
#         message = messaging.Message(
#             notification=messaging.Notification(
#                 title=title,
#                 body=body,
#             ),
#             token=device.fcm_token,
#         )
        
#         try:
#             response = messaging.send(message)
#             NotificationLog.objects.create(
#                 user=user,
#                 title=title,
#                 body=body,
#                 type=notification_type,
#                 success=True
#             )
#         except Exception as e:
#             NotificationLog.objects.create(
#                 user=user,
#                 title=title,
#                 body=body,
#                 type=notification_type,
#                 success=False,
#                 error_message=str(e)
#             )

# # notification/tasks.py
# from celery import shared_task
# from django.contrib.auth.models import User
# from django.utils import timezone
# from datetime import datetime, time
# from .utils import send_push_notification
# from health_logs.models import HealthLog  # Assuming this is your health log model

# @shared_task
# def send_daily_reminders():
#     reminder_times = [
#         time(8, 0),   # 8:00 AM
#         time(13, 0),  # 1:00 PM
#         time(19, 0),  # 7:00 PM
#     ]
    
#     current_time = timezone.localtime().time()
#     current_date = timezone.localtime().date()
    
#     for reminder_time in reminder_times:
#         if reminder_time.hour == current_time.hour:
#             users = User.objects.filter(devices__isnull=False).distinct()
            
#             for user in users:
#                 # Check if user has logged for any child today
#                 has_logs = HealthLog.objects.filter(
#                     parent=user,
#                     created_at__date=current_date
#                 ).exists()
                
#                 if not has_logs:
#                     send_push_notification(
#                         user=user,
#                         title="Health Log Reminder",
#                         body="Please log your child's health information for today.",
#                         notification_type="REMINDER"
#                     )

# # notification/management/commands/generate_reports.py
# from django.core.management.base import BaseCommand
# from django.utils import timezone
# from notification.utils import send_push_notification
# from health_logs.models import HealthLog

# class Command(BaseCommand):
#     help = 'Generates daily reports and sends warning notifications'

#     def handle(self, *args, **kwargs):
#         current_date = timezone.localtime().date()
#         users = User.objects.filter(devices__isnull=False).distinct()
        
#         for user in users:
#             # Check if user has any logs for their children
#             has_logs = HealthLog.objects.filter(
#                 parent=user,
#                 created_at__date=current_date
#             ).exists()
            
#             if not has_logs:
#                 send_push_notification(
#                     user=user,
#                     title="Missed Health Log Warning",
#                     body="No health logs were recorded for your child today. Please add a log.",
#                     notification_type="WARNING"
#                 )
                
#         self.stdout.write(self.style.SUCCESS('Successfully generated reports and sent warnings'))

# # notification/celery.py (add to your app's celery config)
# from celery.schedules import crontab

# CELERY_BEAT_SCHEDULE = {
#     'send-daily-reminders': {
#         'task': 'notification.tasks.send_daily_reminders',
#         'schedule': crontab(minute=0, hour='8,13,19'),  # Runs at 8AM, 1PM, 7PM
#     },
# }

# # settings.py additions
# INSTALLED_APPS += [
#     'notification',
#     'django_celery_beat',
# ]

# # Add Firebase credentials path
# FIREBASE_CREDENTIALS = '/path/to/your/firebase-adminsdk.json'

# # notification/admin.py
# from django.contrib import admin
# from .models import Device, NotificationLog

# @admin.register(Device)
# class DeviceAdmin(admin.ModelAdmin):
#     list_display = ('user', 'fcm_token', 'created_at', 'updated_at')
#     search_fields = ('user__username', 'fcm_token')
#     list_filter = ('created_at',)

# @admin.register(NotificationLog)
# class NotificationLogAdmin(admin.ModelAdmin):
#     list_display = ('user', 'type', 'sent_at', 'success')
#     search_fields = ('user__username', 'title', 'body')
#     list_filter = ('type', 'success', 'sent_at')

# # notification/views.py (for device registration)
# from django.views.decorators.http import require_POST
# from django.http import JsonResponse
# from .models import Device
# from django.contrib.auth.decorators import login_required

# @require_POST
# @login_required
# def register_device(request):
#     fcm_token = request.POST.get('fcm_token')
#     if not fcm_token:
#         return JsonResponse({'error': 'FCM token required'}, status=400)
    
#     device, created = Device.objects.update_or_create(
#         user=request.user,
#         fcm_token=fcm_token
#     )
    
#     return JsonResponse({
#         'status': 'success',
#         'created': created
#     })

# # notification/urls.py
# from django.urls import path
# from . import views

# urlpatterns = [
#     path('register-device/', views.register_device, name='register_device'),
# ]