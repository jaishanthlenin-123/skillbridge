from rest_framework import serializers
from .models import Job, JobRequirement

class JobRequirementSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='skill.category', read_only=True, default='other')

    class Meta:
        model = JobRequirement
        fields = ('id', 'skill_name', 'category', 'is_mandatory', 'importance_weight', 'evidence_text')

class JobListSerializer(serializers.ModelSerializer):
    requirements_count = serializers.IntegerField(source='requirements.count', read_only=True)

    class Meta:
        model = Job
        fields = ('id', 'title', 'company_name', 'source_url', 'requirements_count', 'created_at', 'updated_at')
        read_only_fields = fields

class JobDetailSerializer(serializers.ModelSerializer):
    requirements = JobRequirementSerializer(many=True, read_only=True)

    class Meta:
        model = Job
        fields = ('id', 'title', 'company_name', 'description', 'source_url', 'requirements', 'created_at', 'updated_at')
        read_only_fields = ('id', 'requirements', 'created_at', 'updated_at')

class JobCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = ('id', 'title', 'company_name', 'description', 'source_url')
