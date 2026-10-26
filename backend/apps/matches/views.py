from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from drf_spectacular.utils import extend_schema

from .models import MatchResult, MatchSkillResult
from .serializers import MatchCreateSerializer, MatchResultListSerializer, MatchResultDetailSerializer
from .ml_client import request_ml_service_match
from apps.resumes.models import Resume, Skill
from apps.jobs.models import Job
from apps.audit.services import log_audit_event

class MatchListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: MatchResultListSerializer(many=True)})
    def get(self, request):
        matches = MatchResult.objects.filter(owner=request.user).order_by('-created_at')
        serializer = MatchResultListSerializer(matches, many=True)
        return Response(serializer.data)

    @extend_schema(request=MatchCreateSerializer, responses={201: MatchResultDetailSerializer})
    def post(self, request):
        serializer = MatchCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        resume_id = serializer.validated_data['resume_id']
        job_id = serializer.validated_data['job_id']

        # Enforce resource ownership
        resume = get_object_or_404(Resume, id=resume_id, owner=request.user)
        job = get_object_or_404(Job, id=job_id, owner=request.user)

        # Prepare payload for ML match
        resume_skills_data = [
            {
                'skill_name': s.skill_name,
                'evidence_text': s.evidence_text,
                'confidence': s.confidence
            }
            for s in resume.skills.all()
        ]

        job_reqs_data = [
            {
                'skill_name': r.skill_name,
                'is_mandatory': r.is_mandatory,
                'importance_weight': r.importance_weight,
                'evidence_text': r.evidence_text
            }
            for r in job.requirements.all()
        ]

        # Call ML Service (with automatic fallback)
        ml_result = request_ml_service_match(
            resume_skills=resume_skills_data,
            job_requirements=job_reqs_data,
            resume_text=resume.raw_text,
            job_description=job.description
        )

        match_obj = MatchResult.objects.create(
            owner=request.user,
            resume=resume,
            job=job,
            overall_score=ml_result['overall_score'],
            weighted_coverage_score=ml_result['weighted_coverage_score'],
            coverage_score=ml_result['coverage_score'],
            semantic_score=ml_result['semantic_score'],
            model_version=ml_result.get('model_version', 'all-MiniLM-L6-v2'),
            scoring_config_version=ml_result.get('scoring_config_version', '1.0.0'),
            weights_used=ml_result.get('weights_used', {}),
            structured_explanation=ml_result.get('structured_explanation', {}),
            used_fallback=ml_result.get('used_fallback', False)
        )

        # Populate skill results
        for item in ml_result.get('skill_evaluations', []):
            canonical_skill = Skill.objects.filter(name__iexact=item['skill_name']).first()
            MatchSkillResult.objects.create(
                match=match_obj,
                skill=canonical_skill,
                skill_name=item['skill_name'],
                status=item['status'],
                is_mandatory=item.get('is_mandatory', True),
                match_value=item.get('match_value', 0.0),
                supporting_evidence=item.get('supporting_evidence', '')
            )

        log_audit_event(
            user=request.user,
            event_type='MATCH_GENERATED',
            metadata={
                'match_id': str(match_obj.id),
                'score': match_obj.overall_score,
                'fallback': match_obj.used_fallback
            }
        )

        return Response(MatchResultDetailSerializer(match_obj).data, status=status.HTTP_201_CREATED)

class MatchDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        match = get_object_or_404(MatchResult, id=pk, owner=request.user)
        return Response(MatchResultDetailSerializer(match).data)

    def delete(self, request, pk):
        match = get_object_or_404(MatchResult, id=pk, owner=request.user)
        match.delete()
        return Response({'message': 'Match record deleted.'}, status=status.HTTP_200_OK)

class MatchReportExportView(views.APIView):
    """
    Exports a clean, printable HTML audit report.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        match = get_object_or_404(MatchResult, id=pk, owner=request.user)
        serializer = MatchResultDetailSerializer(match)
        data = serializer.data

        matched_html = "".join(f"<li><strong>{s['skill_name']}</strong> — {s['supporting_evidence']}</li>" for s in data['matched_skills']) or "<li>None</li>"
        missing_html = "".join(f"<li><strong>{s['skill_name']}</strong> ({'Mandatory' if s['is_mandatory'] else 'Preferred'})</li>" for s in data['missing_skills']) or "<li>None</li>"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>SkillBridge Match Report - {match.job.title}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 800px; margin: 40px auto; padding: 20px; }}
        h1 {{ color: #4338ca; border-bottom: 2px solid #e2e8f0; padding-bottom: 10px; }}
        .score-box {{ background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; margin: 20px 0; }}
        .score-big {{ font-size: 42px; font-weight: 800; color: #4338ca; }}
        .grid {{ display: flex; gap: 20px; margin: 20px 0; }}
        .col {{ flex: 1; padding: 15px; border-radius: 6px; }}
        .matched {{ background: #f0fdf4; border: 1px solid #bbf7d0; }}
        .missing {{ background: #fef2f2; border: 1px solid #fecaca; }}
        .footer {{ font-size: 12px; color: #64748b; margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
    </style>
</head>
<body>
    <h1>SkillBridge Resume Intelligence Report</h1>
    <p><strong>Candidate Resume:</strong> {match.resume.title}</p>
    <p><strong>Target Position:</strong> {match.job.title} {f'at {match.job.company_name}' if match.job.company_name else ''}</p>
    <p><strong>Evaluation Date:</strong> {match.created_at.strftime('%B %d, %Y %H:%M UTC')}</p>
    
    <div class="score-box">
        <div>Overall Explainable Match Score:</div>
        <div class="score-big">{match.overall_score:.1f}%</div>
        <p><strong>Score Breakdown:</strong> Requirement-Weighted: {match.weighted_coverage_score:.1f}% | Canonical Overlap: {match.coverage_score:.1f}% | Semantic: {match.semantic_score:.1f}%</p>
        <p><em>{data['structured_explanation'].get('summary', '')}</em></p>
    </div>

    <div class="grid">
        <div class="col matched">
            <h3>Evidenced Skills ({len(data['matched_skills'])})</h3>
            <ul>{matched_html}</ul>
        </div>
        <div class="col missing">
            <h3>Identified Skill Gaps ({len(data['missing_skills'])})</h3>
            <ul>{missing_html}</ul>
        </div>
    </div>

    <div class="footer">
        <p>Engine Version: {match.model_version} | Config Version: {match.scoring_config_version} | Fallback Mode: {'Yes' if match.used_fallback else 'No'}</p>
        <p>Notice: This report provides objective skill evidence mapping between document text and requirement criteria. It does not replace human evaluation or hiring discretion.</p>
    </div>
</body>
</html>"""
        response = HttpResponse(html, content_type='text/html')
        response['Content-Disposition'] = f'inline; filename="skillbridge_report_{match.id}.html"'
        return response
