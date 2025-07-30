from django.db import models


from core.models import Therapist, Parent


class Availability(models.Model):
    therapist = models.ForeignKey(Therapist, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.therapist} - {self.start_time} to {self.end_time}"


class Appointment(models.Model):
    parent = models.ForeignKey(Parent, on_delete=models.CASCADE, related_name='appointments')
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Appointment with {self.availability.therapist} by {self.parent} ({self.status})"
