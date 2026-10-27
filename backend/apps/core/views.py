import os
import requests
from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db import connection
from django.conf import settings
from config.errors import ERROR_REGISTRY, get_error_info

class HealthCheckView(views.APIView):
    """
    Liveness health check endpoint.
    Indicates whether the application process is running and accepting HTTP requests.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'status': 'healthy',
            'application': 'SkillBridge API',
            'environment': 'development' if settings.DEBUG else 'production',
            'request_id': getattr(request, 'request_id', 'unknown'),
        }, status=status.HTTP_200_OK)

class ReadinessCheckView(views.APIView):
    """
    Readiness health check endpoint.
    Verifies that required backing services (database, ML service) are reachable.
    Reports status of optional AI integrations without leaking secrets.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        checks = {
            'database': {'status': 'down'},
            'ml_service': {'status': 'unknown'},
            'gemini_llm': {'configured': False},
            'mongodb_atlas': {'configured': False},
        }

        # 1. Check Primary Relational Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    checks['database'] = {
                        'status': 'up',
                        'engine': connection.vendor
                    }
        except Exception as e:
            checks['database'] = {'status': 'down', 'error': str(e)}

        # 2. Check ML Microservice
        ml_url = getattr(settings, 'ML_SERVICE_URL', 'http://127.0.0.1:8001')
        try:
            resp = requests.get(f"{ml_url}/internal/v1/health/", timeout=3.0)
            if resp.status_code == 200:
                checks['ml_service'] = {'status': 'up', 'url': ml_url}
            else:
                checks['ml_service'] = {'status': 'degraded', 'http_code': resp.status_code}
        except Exception:
            checks['ml_service'] = {'status': 'down', 'fallback_active': True}

        # 3. Check Optional Integrations (Gemini & MongoDB)
        gemini_key = os.getenv('GEMINI_API_KEY', '').strip()
        checks['gemini_llm'] = {
            'configured': bool(gemini_key),
            'model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
            'mode': 'live_genai' if gemini_key else 'deterministic_faq_fallback'
        }

        mongo_uri = os.getenv('MONGODB_URI', '').strip()
        checks['mongodb_atlas'] = {
            'configured': bool(mongo_uri),
            'database': os.getenv('MONGODB_DATABASE', 'skillbridge'),
            'mode': 'persistent_atlas' if mongo_uri else 'in_memory_or_disabled'
        }

        overall_ready = checks['database']['status'] == 'up'
        http_status = status.HTTP_200_OK if overall_ready else status.HTTP_503_SERVICE_UNAVAILABLE

        return Response({
            'ready': overall_ready,
            'checks': checks,
            'request_id': getattr(request, 'request_id', 'unknown'),
        }, status=http_status)

class ErrorRegistryListView(views.APIView):
    """
    Exposes the centralized Error Code Registry for frontend inspection and assistant explanations.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({
            'count': len(ERROR_REGISTRY),
            'errors': list(ERROR_REGISTRY.values())
        })

class ErrorRegistryDetailView(views.APIView):
    """
    Detailed lookup for a specific error code (e.g. 404 or SB-1001).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, code):
        info = get_error_info(code)
        return Response(info)
