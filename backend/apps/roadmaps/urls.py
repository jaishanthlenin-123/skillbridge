from django.urls import path
from .views import RoadmapListCreateView, RoadmapDetailView, RoadmapItemToggleView

urlpatterns = [
    path('', RoadmapListCreateView.as_view(), name='roadmap-list-create'),
    path('<uuid:pk>/', RoadmapDetailView.as_view(), name='roadmap-detail'),
    path('<uuid:roadmap_id>/items/<uuid:item_id>/', RoadmapItemToggleView.as_view(), name='roadmap-item-toggle'),
]
