from django.urls import path
from .views import GitHubProfileInsightsView

urlpatterns = [
    path('github/', GitHubProfileInsightsView.as_view(), name='github-insights'),
]
