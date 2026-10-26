from rest_framework import serializers
from .models import MatchResult, MatchSkillResult
from apps.resumes.serializers import ResumeListSerializer
from apps.jobs.serializers import JobListSerializer

class MatchSkillResultSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = MatchSkillResult
        fields = ('id', 'skill_name', 'status', 'status_display', 'is_mandatory', 'match_value', 'supporting_evidence')

class MatchResultListSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source='resume.title', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)

    class Meta:
        model = MatchResult
        fields = (
            'id', 'resume', 'job', 'resume_title', 'job_title', 'company_name',
            'overall_score', 'weighted_coverage_score', 'coverage_score', 'semantic_score',
            'used_fallback', 'created_at'
        )

class MatchResultDetailSerializer(serializers.ModelSerializer):
    resume_title = serializers.CharField(source='resume.title', read_only=True)
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    skill_results = MatchSkillResultSerializer(many=True, read_only=True)

    matched_skills = serializers.SerializerMethodField()
    related_skills = serializers.SerializerMethodField()
    missing_skills = serializers.SerializerMethodField()
    needs_review_skills = serializers.SerializerMethodField()

    class Meta:
        model = MatchResult
        fields = (
            'id', 'resume', 'job', 'resume_title', 'job_title', 'company_name',
            'overall_score', 'weighted_coverage_score', 'coverage_score', 'semantic_score',
            'model_version', 'scoring_config_version', 'weights_used',
            'structured_explanation', 'used_fallback', 'skill_results',
            'matched_skills', 'related_skills', 'missing_skills', 'needs_review_skills',
            'created_at'
        )

    def get_matched_skills(self, obj):
        return MatchSkillResultSerializer(obj.skill_results.filter(status='MATCHED'), many=True).data

    def get_related_skills(self, obj):
        return MatchSkillResultSerializer(obj.skill_results.filter(status='RELATED'), many=True).data

    def get_missing_skills(self, obj):
        return MatchSkillResultSerializer(obj.skill_results.filter(status='MISSING'), many=True).data

    def get_needs_review_skills(self, obj):
        return MatchSkillResultSerializer(obj.skill_results.filter(status='NEEDS_REVIEW'), many=True).data

class MatchCreateSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField(required=True)
    job_id = serializers.UUIDField(required=True)
