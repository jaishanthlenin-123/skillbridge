from rest_framework import serializers
from .models import Resume, ResumeSection, ResumeSkill, Skill, SkillAlias

class SkillSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = ('id', 'name', 'category', 'category_display', 'description')

class ResumeSkillSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='skill.category', read_only=True, default='other')

    class Meta:
        model = ResumeSkill
        fields = ('id', 'skill_name', 'category', 'evidence_text', 'extraction_method', 'confidence')

class ResumeSectionSerializer(serializers.ModelSerializer):
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)

    class Meta:
        model = ResumeSection
        fields = ('id', 'section_type', 'section_type_display', 'content', 'structured_metadata', 'order_index')

class ResumeListSerializer(serializers.ModelSerializer):
    skills_count = serializers.IntegerField(source='skills.count', read_only=True)
    parsing_status_display = serializers.CharField(source='get_parsing_status_display', read_only=True)

    class Meta:
        model = Resume
        fields = (
            'id', 'title', 'original_filename', 'file_size_bytes', 'mime_type',
            'parsing_status', 'parsing_status_display', 'error_details', 'skills_count',
            'created_at', 'updated_at'
        )
        read_only_fields = fields

class ResumeDetailSerializer(serializers.ModelSerializer):
    sections = ResumeSectionSerializer(many=True, read_only=True)
    skills = ResumeSkillSerializer(many=True, read_only=True)
    parsing_status_display = serializers.CharField(source='get_parsing_status_display', read_only=True)

    class Meta:
        model = Resume
        fields = (
            'id', 'title', 'original_filename', 'file_size_bytes', 'mime_type',
            'raw_text', 'parsing_status', 'parsing_status_display', 'error_details',
            'sections', 'skills', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'original_filename', 'file_size_bytes', 'mime_type', 'parsing_status', 'created_at', 'updated_at')

class ResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    title = serializers.CharField(max_length=255, required=False, default='')

class ResumeSkillEditSerializer(serializers.Serializer):
    skills = serializers.ListField(
        child=serializers.CharField(max_length=150),
        help_text="Updated list of canonical skill names for this resume"
    )
