from django.db import models


from core.models import ChildProfile


# ======================= LOG COMPONENTS ============================
class HeartBeat(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='heartbeats')
    bpm = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.bpm} BPM for {self.child.full_name}"

class Behavior(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='behaviors')
    mood = models.CharField(max_length=100)
    energy_level = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Mood: {self.mood}, Energy: {self.energy_level} for {self.child.full_name}"

class Food(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='foods')
    food_type = models.CharField(max_length=100)
    calories = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.food_type} ({self.calories} cal) for {self.child.full_name}"

class Sleep(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='sleeps')
    hours = models.FloatField()
    sleep_quality = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.hours} hrs, Quality: {self.sleep_quality} for {self.child.full_name}"

class BloodPressure(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='blood_pressures')
    systolic = models.FloatField()
    dystolic = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.systolic}/{self.dystolic} mmHg for {self.child.full_name}"

class ScratchNotes(models.Model):
    child = models.ForeignKey(ChildProfile, on_delete=models.CASCADE, related_name='scratch_notes')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note at {self.created_at} is {self.text}"