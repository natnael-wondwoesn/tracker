# Create your views here.
from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from core.models import ChildProfile
from .models import  HeartBeat, Behavior, Food, Sleep, BloodPressure, ScratchNotes
from .serializers import (
    ChildSerializer, HeartBeatSerializer, BehaviorSerializer,
    FoodSerializer, SleepSerializer, BloodPressureSerializer, ScratchNotesSerializer
)
from django.utils import timezone
from datetime import timedelta



class ChildViewSet(viewsets.ModelViewSet):
    serializer_class = ChildSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return children belonging to the authenticated user
        return ChildProfile.objects.filter(parent=self.request.user)

    def perform_create(self, serializer):
        # Automatically set the parent to the authenticated user
        serializer.save(parent=self.request.user)

class HeartBeatViewSet(viewsets.ModelViewSet):
    serializer_class = HeartBeatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return heartbeats for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return HeartBeat.objects.filter(child__id=child_id, child__parent=self.request.user)
        return HeartBeat.objects.none()
        

    def perform_create(self, serializer):
        # Ensure the child belongs to the authenticated user
        serializer.save()

class BehaviorViewSet(viewsets.ModelViewSet):
    serializer_class = BehaviorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return behaviors for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return Behavior.objects.filter(child__id=child_id, child__parent=self.request.user)
        return Behavior.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class FoodViewSet(viewsets.ModelViewSet):
    serializer_class = FoodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return foods for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return Food.objects.filter(child__id=child_id, child__parent=self.request.user)
        return Food.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class SleepViewSet(viewsets.ModelViewSet):
    serializer_class = SleepSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return sleeps for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return Sleep.objects.filter(child__id=child_id, child__parent=self.request.user)
        return Sleep.objects.none()
    def perform_create(self, serializer):
        serializer.save()

class BloodPressureViewSet(viewsets.ModelViewSet):
    serializer_class = BloodPressureSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return blood pressures for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return BloodPressure.objects.filter(child__id=child_id, child__parent=self.request.user)
        return BloodPressure.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class ScratchNotesViewSet(viewsets.ModelViewSet):
    serializer_class = ScratchNotesSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Only return scratch notes for the user's children
        child_id = self.request.query_params.get('child')
        if child_id:
            return ScratchNotes.objects.filter(child__id=child_id, child__parent=self.request.user)
        return ScratchNotes.objects.none()

    def perform_create(self, serializer):
        serializer.save()

class DashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Get optional query parameter for filtering by child
        child_id = request.query_params.get('child')
        
       

        # Base filter for related models (excluding Child for now)
        queryset_filter = {}
        if child_id:
            queryset_filter['child_id'] = child_id

        queryset_filter['child__parent'] = self.request.user  # Ensure only user's children
        # Aggregate data for all models
        data = {
            'heartbeats': HeartBeatSerializer(
                HeartBeat.objects.filter(**queryset_filter), many=True
            ).data,
            'behaviors': BehaviorSerializer(
                Behavior.objects.filter(**queryset_filter), many=True
            ).data,
            'foods': FoodSerializer(
                Food.objects.filter(**queryset_filter), many=True
            ).data,
            'sleeps': SleepSerializer(
                Sleep.objects.filter(**queryset_filter), many=True
            ).data,
            'bloodpressures': BloodPressureSerializer(
                BloodPressure.objects.filter(**queryset_filter), many=True
            ).data,
            'scratchnotes': ScratchNotesSerializer(
                ScratchNotes.objects.filter(**queryset_filter), many=True
            ).data,
        }
        return Response(data)