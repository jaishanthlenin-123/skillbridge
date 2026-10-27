from rest_framework import views, permissions, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from .github import fetch_github_user_profile

class GitHubProfileInsightsView(views.APIView):
    """
    Fetches GitHub developer insights to correlate verified public code with skills.
    Publicly accessible with bounded timeouts and safe fallbacks.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter('username', str, required=True, description='GitHub username or handle')
        ]
    )
    def get(self, request):
        username = request.query_params.get('username', '').strip()
        if not username:
            return Response(
                {'error': 'Query parameter "username" is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = fetch_github_user_profile(username)
        if data.get('status') == 'not_found':
            return Response(data, status=status.HTTP_404_NOT_FOUND)
        if data.get('status') == 'rate_limited':
            return Response(data, status=status.HTTP_429_TOO_MANY_REQUESTS)
        if data.get('status') in ('timeout', 'unavailable'):
            return Response(data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(data, status=status.HTTP_200_OK)
