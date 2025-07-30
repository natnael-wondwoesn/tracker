from rest_framework import serializers

from core.models import ChildProfile
from .models import HeartBeat, Behavior, Food, Sleep, BloodPressure, ScratchNotes

class ChildSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChildProfile
        fields = ['id', 'full_name', 'created_at']

class HeartBeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeartBeat
        fields = ['id', 'child', 'bpm', 'created_at']

class BehaviorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Behavior
        fields = ['id', 'child', 'mood', 'energy_level', 'created_at']

class FoodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Food
        fields = ['id', 'child', 'food_type', 'calories', 'created_at']

class SleepSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sleep
        fields = ['id', 'child', 'hours', 'sleep_quality', 'created_at']

class BloodPressureSerializer(serializers.ModelSerializer):
    class Meta:
        model = BloodPressure
        fields = ['id', 'child', 'systolic', 'dystolic', 'created_at']

class ScratchNotesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScratchNotes
        fields = ['id', 'child', 'text', 'created_at']