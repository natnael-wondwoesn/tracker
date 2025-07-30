from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChildViewSet, HeartBeatViewSet, BehaviorViewSet, FoodViewSet, SleepViewSet, BloodPressureViewSet, ScratchNotesViewSet, DashboardView

router = DefaultRouter()
router.register(r'children', ChildViewSet, basename='child')
router.register(r'heartbeats', HeartBeatViewSet, basename='heartbeat')
router.register(r'behaviors', BehaviorViewSet, basename='behavior')
router.register(r'foods', FoodViewSet, basename='food')
router.register(r'sleeps', SleepViewSet, basename='sleep')
router.register(r'bloodpressures', BloodPressureViewSet, basename='bloodpressure')
router.register(r'scratchnotes', ScratchNotesViewSet, basename='scratchnotes')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/dashboard/', DashboardView.as_view(), name='dashboard'),
]