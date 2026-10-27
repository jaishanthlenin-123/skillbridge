from django.urls import path
from .views import SupportTicketListCreateView, SupportTicketDetailView, SupportTicketLookupView

urlpatterns = [
    path('', SupportTicketListCreateView.as_view(), name='support-ticket-list-create'),
    path('lookup/', SupportTicketLookupView.as_view(), name='support-ticket-lookup'),
    path('<uuid:pk>/', SupportTicketDetailView.as_view(), name='support-ticket-detail'),
]
