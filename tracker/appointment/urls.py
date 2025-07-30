from rest_framework.routers import DefaultRouter
from .views import AvailabilityViewSet, AppointmentViewSet

router = DefaultRouter()
router.register(r'availabilities', AvailabilityViewSet, basename='availability')
router.register(r'appointments', AppointmentViewSet, basename='appointment')

urlpatterns = router.urls
