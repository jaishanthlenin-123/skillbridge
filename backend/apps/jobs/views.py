from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Job
from .serializers import JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer
from .extractor import extract_job_requirements
from apps.audit.services import log_audit_event

class JobListCreateView(views.APIView):
    """
    List user-owned and sample jobs, or create a new custom job.
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @extend_schema(
        parameters=[
            OpenApiParameter('q', str, description='Search keyword in title, company, description, or location'),
            OpenApiParameter('experience_level', str, description='Filter by experience level'),
            OpenApiParameter('employment_type', str, description='Filter by employment type'),
            OpenApiParameter('is_sample', bool, description='Filter specifically for sample or custom jobs'),
        ],
        responses={200: JobListSerializer(many=True)}
    )
    def get(self, request):
        if request.user.is_authenticated:
            queryset = Job.objects.filter(Q(owner=request.user) | Q(is_sample=True))
        else:
            queryset = Job.objects.filter(is_sample=True)

        q = request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(company_name__icontains=q) |
                Q(description__icontains=q) |
                Q(location__icontains=q)
            )

        exp_level = request.query_params.get('experience_level')
        if exp_level:
            queryset = queryset.filter(experience_level__iexact=exp_level)

        emp_type = request.query_params.get('employment_type')
        if emp_type:
            queryset = queryset.filter(employment_type__iexact=emp_type)

        is_sample = request.query_params.get('is_sample')
        if is_sample is not None:
            is_sample_bool = is_sample.lower() in ('true', '1', 't')
            queryset = queryset.filter(is_sample=is_sample_bool)

        jobs = queryset.order_by('-is_sample', '-created_at')
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)

    @extend_schema(request=JobCreateUpdateSerializer, responses={201: JobDetailSerializer})
    def post(self, request):
        serializer = JobCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(owner=request.user, is_sample=False)
            extract_job_requirements(job)
            job.refresh_from_db()

            log_audit_event(
                user=request.user,
                event_type='JOB_CREATED',
                metadata={'job_id': str(job.id), 'title': job.title}
            )

            return Response(JobDetailSerializer(job).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class JobDetailView(views.APIView):
    """
    Retrieve, update, or delete a job record.
    """
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def get_object(self, request, pk):
        if request.user.is_authenticated:
            job = get_object_or_404(Job, Q(id=pk) & (Q(owner=request.user) | Q(is_sample=True)))
        else:
            job = get_object_or_404(Job, id=pk, is_sample=True)
        return job

    @extend_schema(responses={200: JobDetailSerializer})
    def get(self, request, pk):
        job = self.get_object(request, pk)
        return Response(JobDetailSerializer(job).data)

    @extend_schema(request=JobCreateUpdateSerializer, responses={200: JobDetailSerializer})
    def patch(self, request, pk):
        job = self.get_object(request, pk)
        if job.is_sample and not request.user.is_staff:
            return Response(
                {'detail': 'System sample jobs cannot be modified.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if job.owner != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to edit this job.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobCreateUpdateSerializer(job, data=request.data, partial=True)
        if serializer.is_valid():
            job = serializer.save()
            if 'description' in request.data:
                extract_job_requirements(job)
                job.refresh_from_db()
            return Response(JobDetailSerializer(job).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        job = self.get_object(request, pk)
        if job.is_sample and not request.user.is_staff:
            return Response(
                {'detail': 'System sample jobs cannot be deleted.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if job.owner != request.user and not request.user.is_staff:
            return Response(
                {'detail': 'You do not have permission to delete this job.'},
                status=status.HTTP_403_FORBIDDEN
            )

        job_id_str = str(job.id)
        job.delete()

        log_audit_event(
            user=request.user,
            event_type='JOB_DELETED',
            metadata={'job_id': job_id_str}
        )
        return Response({'message': 'Job description successfully deleted.'}, status=status.HTTP_200_OK)
