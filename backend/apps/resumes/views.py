from rest_framework import status, views, permissions
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema

from .models import Resume, ResumeSkill, Skill, ExtractionMethod
from .serializers import (
    ResumeListSerializer, ResumeDetailSerializer, ResumeUploadSerializer,
    ResumeSkillEditSerializer, SkillSerializer
)
from .storage import validate_and_save_private_file, delete_private_file
from .parser import process_resume_document
from apps.audit.services import log_audit_event

class ResumeListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(responses={200: ResumeListSerializer(many=True)})
    def get(self, request):
        resumes = Resume.objects.filter(owner=request.user).order_by('-created_at')
        serializer = ResumeListSerializer(resumes, many=True)
        return Response(serializer.data)

    @extend_schema(request=ResumeUploadSerializer, responses={201: ResumeDetailSerializer})
    def post(self, request):
        serializer = ResumeUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data['file']
        title = serializer.validated_data.get('title') or uploaded_file.name

        from apps.accounts.guest import is_guest_user, GUEST_MAX_RESUMES
        if is_guest_user(request.user):
            existing_count = Resume.objects.filter(owner=request.user).count()
            if existing_count >= GUEST_MAX_RESUMES:
                return Response({
                    'error': f'Guest upload limit reached (maximum {GUEST_MAX_RESUMES} resumes per guest session). Please delete an existing upload or create an account to store more resumes.'
                }, status=status.HTTP_400_BAD_REQUEST)

        try:
            stored_meta = validate_and_save_private_file(uploaded_file, str(request.user.id))
        except ValidationError as e:
            return Response({'error': str(e.message if hasattr(e, 'message') else e)}, status=status.HTTP_400_BAD_REQUEST)

        resume = Resume.objects.create(
            owner=request.user,
            title=title,
            original_filename=stored_meta['original_filename'],
            private_storage_key=stored_meta['storage_key'],
            file_hash=stored_meta['file_hash'],
            file_size_bytes=stored_meta['file_size'],
            mime_type=stored_meta['mime_type'],
        )

        # Trigger extraction
        process_resume_document(resume)
        resume.refresh_from_db()

        log_audit_event(
            user=request.user,
            event_type='RESUME_UPLOADED',
            metadata={'resume_id': str(resume.id), 'filename': resume.original_filename, 'status': resume.parsing_status}
        )

        return Response(ResumeDetailSerializer(resume).data, status=status.HTTP_201_CREATED)

class ResumeDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Resume, id=pk, owner=request.user)

    @extend_schema(responses={200: ResumeDetailSerializer})
    def get(self, request, pk):
        resume = self.get_object(request, pk)
        return Response(ResumeDetailSerializer(resume).data)

    def patch(self, request, pk):
        resume = self.get_object(request, pk)
        if 'title' in request.data:
            resume.title = request.data['title']
            resume.save(update_fields=['title'])
        return Response(ResumeDetailSerializer(resume).data)

    def delete(self, request, pk):
        resume = self.get_object(request, pk)
        storage_key = resume.private_storage_key
        resume_id_str = str(resume.id)
        
        # Purge physical file
        delete_private_file(storage_key)
        
        # Delete record & cascade sections/skills
        resume.delete()

        log_audit_event(
            user=request.user,
            event_type='RESUME_DELETED',
            metadata={'resume_id': resume_id_str}
        )
        return Response({'message': 'Resume and associated storage successfully deleted.'}, status=status.HTTP_200_OK)

class ResumeSkillsUpdateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(request=ResumeSkillEditSerializer, responses={200: ResumeDetailSerializer})
    def post(self, request, pk):
        resume = get_object_or_404(Resume, id=pk, owner=request.user)
        serializer = ResumeSkillEditSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        new_skill_names = set(s.strip() for s in serializer.validated_data['skills'] if s.strip())

        # Sync skills: delete removed, add new
        existing_skills = {rs.skill_name: rs for rs in resume.skills.all()}
        
        for name in list(existing_skills.keys()):
            if name not in new_skill_names:
                existing_skills[name].delete()

        for name in new_skill_names:
            if name not in existing_skills:
                canonical_skill = Skill.objects.filter(name__iexact=name).first()
                ResumeSkill.objects.create(
                    resume=resume,
                    skill=canonical_skill,
                    skill_name=name,
                    evidence_text="Added / Verified by user",
                    extraction_method=ExtractionMethod.USER_EDITED,
                    confidence=1.0
                )

        resume.refresh_from_db()
        return Response(ResumeDetailSerializer(resume).data)

class SkillTaxonomyListView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.all().order_by('category', 'name')
        return Response(SkillSerializer(skills, many=True).data)
