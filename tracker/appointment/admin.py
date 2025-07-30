from django.contrib import admin

from .models import Appointment, Availability

# Register your models here.
admin.site.register(Appointment)
admin.site.register(Availability)