from rest_framework import serializers
from .models import Roadmap, RoadmapItem

class RoadmapItemSerializer(serializers.ModelSerializer):
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)

    class Meta:
        model = RoadmapItem
        fields = (
            'id', 'skill_name', 'priority', 'priority_display', 'estimated_weeks',
            'rationale', 'suggested_project', 'resources', 'is_completed',
            'completed_at', 'order_index'
        )
        read_only_fields = ('id', 'skill_name', 'priority', 'estimated_weeks', 'rationale', 'suggested_project', 'resources', 'order_index')

class RoadmapDetailSerializer(serializers.ModelSerializer):
    items = RoadmapItemSerializer(many=True, read_only=True)
    match_score = serializers.FloatField(source='match.overall_score', read_only=True)
    completed_items_count = serializers.SerializerMethodField()
    total_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Roadmap
        fields = (
            'id', 'match', 'title', 'target_role', 'match_score', 'items',
            'completed_items_count', 'total_items_count', 'created_at', 'updated_at'
        )

    def get_completed_items_count(self, obj):
        return obj.items.filter(is_completed=True).count()

    def get_total_items_count(self, obj):
        return obj.items.count()

class RoadmapListSerializer(serializers.ModelSerializer):
    match_score = serializers.FloatField(source='match.overall_score', read_only=True)
    completed_items_count = serializers.SerializerMethodField()
    total_items_count = serializers.SerializerMethodField()

    class Meta:
        model = Roadmap
        fields = (
            'id', 'match', 'title', 'target_role', 'match_score',
            'completed_items_count', 'total_items_count', 'created_at', 'updated_at'
        )

    def get_completed_items_count(self, obj):
        return obj.items.filter(is_completed=True).count()

    def get_total_items_count(self, obj):
        return obj.items.count()

class RoadmapCreateSerializer(serializers.Serializer):
    match_id = serializers.UUIDField(required=True)
