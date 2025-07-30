from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
# from storages.backends.s3boto3 import S3Boto3Storage
#from django_crypto_fields.fields import models.models.CharField
import uuid



class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class UserRole(models.TextChoices):
    PARENT = 'parent', 'Parent'
    THERAPIST = 'therapist', 'Therapist'
    ADMIN = 'admin', 'Admin'


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    phone_number = models.CharField(max_length=15, unique=True, default='')
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.PARENT)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'role']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_short_name(self):
        return self.first_name

class Parent(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='parent')
    active_child = models.ForeignKey(
        'ChildProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_parent'
    )
    def __str__(self):
        return self.user.get_full_name()

class Therapist(TimeStampedModel):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True, related_name='therapist')
    edu_document = models.FileField(
        upload_to='edu_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    is_verified = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)
    rejected_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name()

class PendingUser(TimeStampedModel):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    phone_number = models.CharField(max_length=15, unique=True, default='')
    password = models.CharField(max_length=128)
    edu_document = models.FileField(
        upload_to='edu_documents/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
    )
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    role = models.CharField(max_length=10, choices=UserRole.choices, default=UserRole.PARENT)
    is_verified = models.BooleanField(default=False)
    admin_approved = models.BooleanField(default=False)
    rejected_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email


class ChildProfile(TimeStampedModel):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    parent = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='children')
    first_name = models.CharField(max_length=30, default='')
    last_name = models.CharField(max_length=30, default='')
    full_name = models.CharField(max_length=61, blank=True, null=True)
    date_of_birth = models.DateField(default=timezone.now)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default='O')
    medical_history = models.FileField(
        upload_to='medical_history/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        blank=True,
        null=True,
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png'])],
        blank=True,
        null=True,
    )

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Delete associated files
        if self.medical_history:
            try:
                self.medical_history.delete(save=False)
            except FileNotFoundError:
                pass
        if self.profile_picture:
            try:
                self.profile_picture.delete(save=False)
            except FileNotFoundError:
                pass
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} (Parent: {self.parent.email})"

    class Meta:
        unique_together = ('parent', 'full_name')
        indexes = [models.Index(fields=['parent'])]
        db_table = 'child_profile'
        verbose_name = 'Child Profile'
        verbose_name_plural = 'Child Profiles'


