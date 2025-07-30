# from fcm_django.models import FCMDevice
# from firebase_admin import messaging
# import firebase_admin
# from django.conf import settings
# from django.utils import timezone
# from .models import Device, NotificationLog

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
