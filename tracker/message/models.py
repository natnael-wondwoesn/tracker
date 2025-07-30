from django.db import models

from core.models import CustomUser

# Create your models here.
class Conversation(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.CharField(blank=True, null=True, max_length=225)
    status = models.CharField(blank=True, null=True, max_length=225)
    created_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f"{self.user.first_name}: {self.message}"