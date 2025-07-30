from django.contrib import admin

# Register your models here.

from .models import *


admin.site.register(HeartBeat)
admin.site.register(BloodPressure)
admin.site.register(Food)
admin.site.register(Sleep)
admin.site.register(ScratchNotes)
admin.site.register(Behavior)