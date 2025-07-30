from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError, NotFound

from core.models import Parent
from .models import Availability, Appointment, Therapist
from .serializers import AvailabilitySerializer, AppointmentSerializer
import logging

logger = logging.getLogger(__name__)

class AvailabilityViewSet(viewsets.ModelViewSet):
    serializer_class = AvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # logger.info(f"Fetching availabilities for user {user.id}, email={user.email}, groups={list(user.groups.values_list('name', flat=True))}")

        try:
            # Check if user has a Therapist instance
            therapist = Therapist.objects.get(user=user)
            # logger.debug(f"User {user.id} has a Therapist instance, returning their availabilities")
            return Availability.objects.filter(therapist=therapist)
        except Therapist.DoesNotExist:
            # logger.debug(f"No Therapist instance found for user {user.id}, returning unbooked availabilities")
            return Availability.objects.filter(is_booked=False)

    def perform_create(self, serializer):
        user = self.request.user
        # logger.info(f"Creating availability for user {user.id}, email={user.email}")

        try:
            # Ensure user has a Therapist instance
            therapist = Therapist.objects.get(user=user)
        except Therapist.DoesNotExist:
            # logger.error(f"No Therapist instance found for user {user.id}, email={user.email}")
            raise ValidationError("Only users with a Therapist profile can create availabilities.")

        try:
            # Ensure validated data is present
            if not serializer.is_valid():
                # logger.error(f"Serializer validation failed for user {user.id}: {serializer.errors}")
                raise ValidationError(serializer.errors)

            start_time = serializer.validated_data.get('start_time')
            end_time = serializer.validated_data.get('end_time')

            if not start_time or not end_time:
                # logger.error(f"Missing start_time or end_time for user {user.id}")
                raise ValidationError("Start time and end time are required.")

            if end_time <= start_time:
                # logger.error(f"Invalid time range for user {user.id}: start_time={start_time}, end_time={end_time}")
                raise ValidationError("End time must be after start time.")

            # Check for overlapping availabilities
            overlapping = Availability.objects.filter(
                therapist=therapist,
                start_time__lte=end_time,
                end_time__gte=start_time,
            )

            if overlapping.exists():
                logger.warning(f"Overlap detected for therapist {therapist.user.email}: {start_time} to {end_time}, conflicting slots: {list(overlapping.values('id', 'start_time', 'end_time'))}")
                raise ValidationError("This time slot overlaps with an existing availability.")

            # Save the availability
            serializer.save(therapist=therapist)
            logger.info(f"Created availability for therapist {therapist.user.email}: {start_time} to {end_time}")

        except ValidationError as e:
            # logger.error(f"Validation error for user {user.id}: {str(e)}")
            raise
        except Exception as e:
            # logger.error(f"Unexpected error creating availability for user {user.id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create availability: {str(e)}")

    def perform_update(self, serializer):
        user = self.request.user
        # logger.info(f"Updating availability for user {user.id}, email={user.email}")

        try:
            # Ensure user has a Therapist instance
            therapist = Therapist.objects.get(user=user)
        except Therapist.DoesNotExist:
            # logger.error(f"No Therapist instance found for user {user.id}, email={user.email}")
            raise ValidationError("Only users with a Therapist profile can update availabilities.")

        try:
            if not serializer.is_valid():
                # logger.error(f"Serializer validation failed for user {user.id}: {serializer.errors}")
                raise ValidationError(serializer.errors)

            start_time = serializer.validated_data.get('start_time')
            end_time = serializer.validated_data.get('end_time')

            if end_time <= start_time:
                # logger.error(f"Invalid time range for update by user {user.id}: start_time={start_time}, end_time={end_time}")
                raise ValidationError("End time must be after start time.")

            overlapping = Availability.objects.filter(
                therapist=therapist,
                start_time__lte=end_time,
                end_time__gte=start_time,
            ).exclude(pk=serializer.instance.pk)

            if overlapping.exists():
                logger.warning(f"Overlap detected on update for therapist {therapist.user.email}: {start_time} to {end_time}, conflicting slots: {list(overlapping.values('id', 'start_time', 'end_time'))}")
                raise ValidationError("This time slot overlaps with an existing availability.")

            serializer.save(therapist=therapist)
            logger.info(f"Updated availability {serializer.instance.id} for therapist {therapist.user.email}")

        except ValidationError as e:
            # logger.error(f"Validation error on update for user {user.id}: {str(e)}")
            raise
        except Exception as e:
            # logger.error(f"Unexpected error updating availability for user {user.id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to update availability: {str(e)}")

    def perform_destroy(self, instance):
        user = self.request.user
        # logger.info(f"Deleting availability {instance.id} for user {user.id}, email={user.email}")

        try:
            therapist = Therapist.objects.get(user=user)
            if instance.therapist != therapist:
                # logger.warning(f"User {user.id} attempted to delete availability {instance.id} belonging to another therapist")
                raise ValidationError("You can only delete your own availabilities.")
        except Therapist.DoesNotExist:
            # logger.error(f"No Therapist instance found for user {user.id}, email={user.email}")
            raise ValidationError("Only users with a Therapist profile can delete availabilities.")

        instance.delete()
        # logger.info(f"Deleted availability {instance.id} by user {user.id}")


class AppointmentViewSet(viewsets.ModelViewSet):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # logger.info(f"Fetching appointments for user {user.id}, email={user.email}, groups={list(user.groups.values_list('name', flat=True))}")

        try:
            # Users with a Therapist instance can access all appointments
            Therapist.objects.get(user=user)
            # logger.debug(f"User {user.id} has a Therapist instance, returning all appointments")
            return Appointment.objects.all()
        except Therapist.DoesNotExist:
            print("No Therapist instance found for user, checking for Parent instance")
            # logger.debug(f"No Therapist instance found for user {user.id}, checking for Parent instance")

        # Non-therapists (parents) access their own appointments
        try:
            parent = Parent.objects.get(user=user)
            # logger.debug(f"User {user.id} is a parent, returning appointments for parent {parent.id}")
            return Appointment.objects.filter(parent=parent)
        except Parent.DoesNotExist:
            # logger.warning(f"No Parent instance found for user {user.id}, email={user.email}")
            return Appointment.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        # logger.info(f"Creating appointment for user {user.id}, email={user.email}")

        try:
            # Non-therapists (parents) create appointments
            parent, created = Parent.objects.get_or_create(user=user)
            # if created:
            #     # logger.info(f"Created new Parent instance for user {user.id}, email={user.email}")

            availability = serializer.validated_data['availability']
            if availability.is_booked:
                # logger.warning(f"Attempt to book already booked slot {availability.id} by user {user.id}, email={user.email}")
                raise ValidationError("This time slot is already booked.")

            availability.is_booked = True
            availability.save()
            serializer.save(parent=parent)
            # logger.info(f"Created appointment for availability {availability.id} by user {user.id}, email={user.email}")

        except ValidationError as e:
            # logger.error(f"Validation error for user {user.id}: {str(e)}")
            raise
        except Exception as e:
            # logger.error(f"Unexpected error creating appointment for user {user.id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to create appointment: {str(e)}")

    def perform_update(self, serializer):
        user = self.request.user
        # logger.info(f"Updating appointment for user {user.id}, email={user.email}")

        try:
            # Non-therapists (parents) update appointments
            parent = Parent.objects.get(user=user)

            availability = serializer.validated_data.get('availability')
            if availability and availability.is_booked and availability != serializer.instance.availability:
                # logger.warning(f"Attempt to update appointment to booked slot {availability.id} by user {user.id}, email={user.email}")
                raise ValidationError("This time slot is already booked.")

            if availability and availability != serializer.instance.availability:
                serializer.instance.availability.is_booked = False
                serializer.instance.availability.save()
                availability.is_booked = True
                availability.save()

            serializer.save(parent=parent)
            # logger.info(f"Updated appointment {serializer.instance.id} by user {user.id}, email={user.email}")

        except Parent.DoesNotExist:
            # logger.error(f"No Parent instance found for user {user.id}, email={user.email}")
            raise ValidationError("User must have a corresponding Parent profile to update an appointment.")
        except ValidationError as e:
            # logger.error(f"Validation error on update for user {user.id}: {str(e)}")
            raise
        except Exception as e:
            # logger.error(f"Unexpected error updating appointment for user {user.id}: {str(e)}", exc_info=True)
            raise ValidationError(f"Failed to update appointment: {str(e)}")

    def perform_destroy(self, instance):
        user = self.request.user
        # logger.info(f"Deleting appointment for user {user.id}, email={user.email}")

        try:
            parent = Parent.objects.get(user=user)
            if instance.parent != parent:
                # logger.warning(f"User {user.id}, email={user.email} attempted to delete appointment {instance.id} not owned by them")
                raise ValidationError("You can only delete your own appointments.")
        except Parent.DoesNotExist:
            # logger.error(f"No Parent instance found for user {user.id}, email={user.email}")
            raise ValidationError("User must have a corresponding Parent profile to delete an appointment.")

        instance.availability.is_booked = False
        instance.availability.save()
        instance.delete()
        # logger.info(f"Deleted appointment {instance.id} by user {user.id}, email={user.email}")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def approve(self, request, pk=None):
        try:
            appointment = self.get_object()
            try:
                Therapist.objects.get(user=request.user)
            except Therapist.DoesNotExist:
                # logger.warning(f"User {request.user.id}, email={request.user.email} without Therapist instance attempted to approve appointment {pk}")
                raise ValidationError("Only users with a Therapist profile can approve appointments.")
            appointment.status = 'approved'
            appointment.save()
            # logger.info(f"Approved appointment {pk} by user {request.user.id}, email={request.user.email}")
            return Response({"status": "approved"}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            logger.warning(f"Attempt to approve non-existent appointment {pk}")
            raise NotFound("Appointment not found")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def reject(self, request, pk=None):
        try:
            appointment = self.get_object()
            try:
                Therapist.objects.get(user=request.user)
            except Therapist.DoesNotExist:
                # logger.warning(f"User {request.user.id}, email={request.user.email} without Therapist instance attempted to reject appointment {pk}")
                raise ValidationError("Only users with a Therapist profile can reject appointments.")
            appointment.status = 'rejected'
            appointment.availability.is_booked = False
            appointment.availability.save()
            appointment.save()
            # logger.info(f"Rejected appointment {pk} by user {request.user.id}, email={request.user.email}")
            return Response({"status": "rejected"}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            logger.warning(f"Attempt to reject non-existent appointment {pk}")
            raise NotFound("Appointment not found")