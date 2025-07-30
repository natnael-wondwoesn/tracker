from rest_framework import serializers
from core.models import Therapist, Parent
from core.serializers import TherapistSerializer, ParentSerializer
from .models import Availability, Appointment

class AvailabilitySerializer(serializers.ModelSerializer):
    therapist = serializers.PrimaryKeyRelatedField(
        queryset=Therapist.objects.all(),  # Adjust to your Therapist model
        write_only=True  # Only used for writing (POST/PUT)
    )
    therapist_detail = serializers.SerializerMethodField(read_only=True)  # For reading therapist details

    class Meta:
        model = Availability
        fields = ['id', 'therapist', 'therapist_detail', 'start_time', 'end_time', 'is_booked']
        read_only_fields = ['is_booked', 'therapist_detail']

    def get_therapist_detail(self, obj):
        # Return full therapist details for GET requests
        return TherapistSerializer(obj.therapist).data

class AppointmentSerializer(serializers.ModelSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Parent.objects.all(),  # Adjust to your Parent model
        write_only=True  # Only used for writing (POST/PUT)
    )
    parent_detail = serializers.SerializerMethodField(read_only=True)  # For reading parent details

    class Meta:
        model = Appointment
        fields = ['id', 'parent', 'parent_detail', 'availability', 'status', 'requested_at']  # Adjust fields as needed
        read_only_fields = ['parent_detail']  # Adjust read-only fields as needed

    def get_parent_detail(self, obj):
        # Return full parent details for GET requests
        return ParentSerializer(obj.parent).data