from django.urls import path
from .views import (
    ReportCreateView,
    ReportListView,
    ReportDetailView
)

urlpatterns = [
    path('', ReportCreateView.as_view(), name='create-report'),
    path('list/', ReportListView.as_view(), name='list-reports'),
    path('<int:pk>/', ReportDetailView.as_view(), name='report-detail')
]
