from django.urls import path
from .views import UserAuditHistoryView

urlpatterns = [
    path('events/', UserAuditHistoryView.as_view(), name='audit-events'),
]
