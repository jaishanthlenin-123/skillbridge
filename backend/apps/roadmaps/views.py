from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema

from .models import Roadmap, RoadmapItem
from .serializers import RoadmapListSerializer, RoadmapDetailSerializer, RoadmapCreateSerializer, RoadmapItemSerializer
from .generator import generate_roadmap_for_match
from apps.matches.models import MatchResult
from apps.audit.services import log_audit_event

class RoadmapListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: RoadmapListSerializer(many=True)})
    def get(self, request):
        roadmaps = Roadmap.objects.filter(owner=request.user).order_by('-created_at')
        serializer = RoadmapListSerializer(roadmaps, many=True)
        return Response(serializer.data)

    @extend_schema(request=RoadmapCreateSerializer, responses={201: RoadmapDetailSerializer})
    def post(self, request):
        serializer = RoadmapCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        match_id = serializer.validated_data['match_id']
        match = get_object_or_404(MatchResult, id=match_id, owner=request.user)

        roadmap = generate_roadmap_for_match(match)

        log_audit_event(
            user=request.user,
            event_type='ROADMAP_GENERATED',
            metadata={'roadmap_id': str(roadmap.id), 'match_id': str(match.id)}
        )

        return Response(RoadmapDetailSerializer(roadmap).data, status=status.HTTP_201_CREATED)

class RoadmapDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Roadmap, id=pk, owner=request.user)

    @extend_schema(responses={200: RoadmapDetailSerializer})
    def get(self, request, pk):
        roadmap = self.get_object(request, pk)
        return Response(RoadmapDetailSerializer(roadmap).data)

    def delete(self, request, pk):
        roadmap = self.get_object(request, pk)
        roadmap.delete()
        return Response({'message': 'Roadmap successfully deleted.'}, status=status.HTTP_200_OK)

class RoadmapItemToggleView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, roadmap_id, item_id):
        roadmap = get_object_or_404(Roadmap, id=roadmap_id, owner=request.user)
        item = get_object_or_404(RoadmapItem, id=item_id, roadmap=roadmap)

        is_completed = request.data.get('is_completed')
        if is_completed is not None:
            item.is_completed = bool(is_completed)
            item.completed_at = timezone.now() if item.is_completed else None
            item.save(update_fields=['is_completed', 'completed_at'])

        return Response(RoadmapItemSerializer(item).data)
