from django.urls import path
from .views import MatchListCreateView, MatchDetailView, MatchReportExportView

urlpatterns = [
    path('', MatchListCreateView.as_view(), name='match-list-create'),
    path('<uuid:pk>/', MatchDetailView.as_view(), name='match-detail'),
    path('<uuid:pk>/report/', MatchReportExportView.as_view(), name='match-report-export'),
]
