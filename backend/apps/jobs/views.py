from rest_framework import status, views, permissions
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema

from .models import Job
from .serializers import JobListSerializer, JobDetailSerializer, JobCreateUpdateSerializer
from .extractor import extract_job_requirements
from apps.audit.services import log_audit_event

class JobListCreateView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(responses={200: JobListSerializer(many=True)})
    def get(self, request):
        jobs = Job.objects.filter(owner=request.user).order_by('-created_at')
        serializer = JobListSerializer(jobs, many=True)
        return Response(serializer.data)

    @extend_schema(request=JobCreateUpdateSerializer, responses={201: JobDetailSerializer})
    def post(self, request):
        serializer = JobCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            job = serializer.save(owner=request.user)
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
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, pk):
        return get_object_or_404(Job, id=pk, owner=request.user)

    @extend_schema(responses={200: JobDetailSerializer})
    def get(self, request, pk):
        job = self.get_object(request, pk)
        return Response(JobDetailSerializer(job).data)

    @extend_schema(request=JobCreateUpdateSerializer, responses={200: JobDetailSerializer})
    def patch(self, request, pk):
        job = self.get_object(request, pk)
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
        job_id_str = str(job.id)
        job.delete()

        log_audit_event(
            user=request.user,
            event_type='JOB_DELETED',
            metadata={'job_id': job_id_str}
        )
        return Response({'message': 'Job description successfully deleted.'}, status=status.HTTP_200_OK)
