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
