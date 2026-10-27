from django.urls import path
from .views import HealthCheckView, ReadinessCheckView, ErrorRegistryListView, ErrorRegistryDetailView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='health-check'),
    path('readiness/', ReadinessCheckView.as_view(), name='readiness-check'),
    path('errors/', ErrorRegistryListView.as_view(), name='error-registry-list'),
    path('errors/<str:code>/', ErrorRegistryDetailView.as_view(), name='error-registry-detail'),
]
