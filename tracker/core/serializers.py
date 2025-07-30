from rest_framework import serializers
from .models import CustomUser,PendingUser, Therapist, Parent, ChildProfile
import random
from datetime import datetime, timedelta
from django.utils import timezone
import re, logging
from django.db.models import Q
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.core.cache import cache
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from django.core.validators import FileExtensionValidator
logger = logging.getLogger(__name__)
CustomUser = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'first_name', 'last_name', 'role', 'is_active']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    edu_document = serializers.FileField(
            required=False,
            validators=[
                FileExtensionValidator(allowed_extensions=['pdf'])
            ]
        )
    class Meta:
        model = PendingUser
        fields = (
            'id', 'email', 'phone_number', 'first_name', 'last_name',
            'role', 'password', 'confirm_password', 'edu_document'
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'confirm_password': {'write_only': True, 'required': True},
            'email': {'required': True},
            'phone_number': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'role': {'required': True},
        }


        def validate_email(self, value):
            if CustomUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email is already registered.")
            if PendingUser.objects.filter(email=value).exists():
                raise serializers.ValidationError("Email is pending verification.")
            return value

        def validate_role(self, value):
            if value not in ['parent', 'therapist']:
                raise serializers.ValidationError("Role must be either 'parent' or 'therapist'.")
            return value

        def validate(self, data):
        # Password match validation
            if data['password'] != data['confirm_password']:
                raise serializers.ValidationError({"confirm_password": "Passwords don't match."})
            # Role-based edu_document validation
            role = data.get('role')
            edu_document = data.get('edu_document')
            if role == 'therapist' and not edu_document:
                raise serializers.ValidationError({"edu_document": "Educational document is required for therapists."})
            if role == 'parent' and edu_document:
                raise serializers.ValidationError({"edu_document": "Educational document is not applicable for parents."})

            return data


class ParentSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()
    class Meta:
        model = Parent
        fields = ['user']
class TherapistSerializer(serializers.ModelSerializer):
    user = UserRegistrationSerializer()

    class Meta:
        model = Therapist
        fields = ['user']
    
    def validate(self, data):
        # Ensure edu_document is provided for therapists
        if not data.get('edu_document'):
            raise serializers.ValidationError({"edu_document": "Educational document is required for therapists."})
        return data

class AdminApprovalSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    action = serializers.ChoiceField(choices=['approve', 'reject'], required=True)
    
    class Meta:
        fields = ['email', 'action']

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if user is None or not user.is_active:
            raise serializers.ValidationError("Invalid email or password.")
        data['user'] = user
        return data
    
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

class ChildProfileSerializer(serializers.ModelSerializer):  
    parent_email = serializers.EmailField(source='parent.email', read_only=True)
    medical_history = serializers.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        allow_null=True,
    )
    profile_picture = serializers.FileField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        allow_null=True,
    )

    class Meta:
        model = ChildProfile
        fields = [
            'id', 'parent_email', 'first_name', 'last_name', 'full_name',
            'date_of_birth', 'gender', 'medical_history', 'profile_picture',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'parent_email', 'full_name', 'created_at', 'updated_at']

    def validate(self, data):
        # Ensure parent is authenticated and has role='parent'
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or request.user.role != 'parent':
            raise serializers.ValidationError("Only authenticated parents can manage child profiles.")
        
        # Validate date_of_birth
        date_of_birth = data.get('date_of_birth')
        if date_of_birth and date_of_birth > timezone.now().date():
            raise serializers.ValidationError({"date_of_birth": "Date of birth cannot be in the future."})
        
        return data
        
