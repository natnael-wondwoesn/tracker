from django.contrib import admin
from django.db import transaction
from .models import PendingUser, CustomUser, Parent, Therapist
from django.core.mail import send_mail
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

@admin.register(PendingUser)
class PendingUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'has_document', 'edu_document_link', 'created_at')
    list_filter = ('role',)
    search_fields = ('email', 'first_name', 'last_name')
    actions = ['approve_therapist', 'reject_therapist']
    readonly_fields = ('edu_document', 'verification_token', 'created_at')

    def has_document(self, obj):
        return bool(obj.edu_document)
    has_document.boolean = True
    has_document.short_description = 'Document Uploaded'

    def edu_document_link(self, obj):
        if obj.edu_document:
            return f'<a href="{obj.edu_document.url}" target="_blank">View Document</a>'
        return '-'
    edu_document_link.allow_tags = True
    edu_document_link.short_description = 'Document'

    def approve_therapist(self, request, queryset):
        for pending_user in queryset:
            if pending_user.role != 'therapist':
                self.message_user(request, f"Cannot approve {pending_user.email}: Not a therapist.")
                continue
            if not pending_user.edu_document:
                self.message_user(request, f"Cannot approve {pending_user.email}: No educational document uploaded.")
                continue
            user = CustomUser.objects.filter(email=pending_user.email).first()
            if not user:
                self.message_user(request, f"Cannot approve {pending_user.email}: User not found.")
                continue
            if user.is_active:
                self.message_user(request, f"Cannot approve {pending_user.email}: User already approved.")
                continue
            try:
                with transaction.atomic():
                    user.is_active = True
                    user.save()
                    Therapist.objects.create(user=user)
                    pending_user.delete()  # edu_document retained in storage
                    send_mail(
                        subject='Account Approved',
                        message='Your therapist account has been approved.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                    logger.info(f'Therapist {user.email} approved via admin')
                    self.message_user(request, f"Approved therapist {user.email}.")
            except Exception as e:
                logger.error(f'Error approving therapist {pending_user.email}: {str(e)}')
                self.message_user(request, f"Failed to approve {pending_user.email}: {str(e)}.")

    approve_therapist.short_description = "Approve selected therapists"

    def reject_therapist(self, request, queryset):
        for pending_user in queryset:
            if pending_user.role != 'therapist':
                self.message_user(request, f"Cannot reject {pending_user.email}: Not a therapist.")
                continue
            user = CustomUser.objects.filter(email=pending_user.email).first()
            if not user:
                self.message_user(request, f"Cannot reject {pending_user.email}: User not found.")
                continue
            try:
                with transaction.atomic():
                    if pending_user.edu_document:
                        try:
                            os.remove(pending_user.edu_document.path)
                        except FileNotFoundError:
                            pass
                    user.delete()
                    pending_user.delete()
                    send_mail(
                        subject='Account Rejected',
                        message='Your therapist account has been rejected.',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[user.email],
                        fail_silently=True,
                    )
                    logger.info(f'Therapist {user.email} rejected via admin')
                    self.message_user(request, f"Rejected therapist {user.email}.")
            except Exception as e:
                logger.error(f'Error rejecting therapist {pending_user.email}: {str(e)}')
                self.message_user(request, f"Failed to reject {pending_user.email}: {str(e)}.")

    reject_therapist.short_description = "Reject selected therapists"


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    readonly_fields = ('password',)
    actions = ['activate_users', 'deactivate_users']

    def activate_users(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f"Activated {updated} users.")

    activate_users.short_description = "Activate selected users"

    def deactivate_users(self, request, queryset):
        updated = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f"Deactivated {updated} users.")

    deactivate_users.short_description = "Deactivate selected users"


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_first_name', 'user_last_name', 'active_child_name')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('user__is_active',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = 'First Name'

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = 'Last Name'

    def active_child_name(self, obj):
        return obj.active_child.full_name if obj.active_child else '-'
    active_child_name.short_description = 'Active Child'


@admin.register(Therapist)
class TherapistAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'user_first_name', 'user_last_name', 'is_active')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_filter = ('user__is_active',)

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email'

    def user_first_name(self, obj):
        return obj.user.first_name
    user_first_name.short_description = 'First Name'

    def user_last_name(self, obj):
        return obj.user.last_name
    user_last_name.short_description = 'Last Name'

    def is_active(self, obj):
        return obj.user.is_active
    is_active.boolean = True
    is_active.short_description = 'Active'