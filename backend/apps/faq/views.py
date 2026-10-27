from rest_framework import views, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import FAQ, FAQCategory
from .serializers import FAQSerializer, FAQCategorySerializer

class FAQListView(views.APIView):
    """
    Public listing and search endpoint for database-backed FAQ items.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter('q', str, description='Search text in question or answer'),
            OpenApiParameter('category', str, description='Filter by category slug or name'),
        ],
        responses={200: FAQSerializer(many=True)}
    )
    def get(self, request):
        queryset = FAQ.objects.filter(is_active=True).select_related('category')
        
        q = request.query_params.get('q', '').strip()
        if q:
            queryset = queryset.filter(Q(question__icontains=q) | Q(answer__icontains=q))

        category = request.query_params.get('category', '').strip()
        if category:
            queryset = queryset.filter(Q(category__slug=category) | Q(category__name__iexact=category))

        serializer = FAQSerializer(queryset, many=True)
        return Response(serializer.data)

class FAQCategoryListView(views.APIView):
    """
    Public listing of available FAQ categories.
    """
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: FAQCategorySerializer(many=True)})
    def get(self, request):
        categories = FAQCategory.objects.all().prefetch_related('faqs')
        serializer = FAQCategorySerializer(categories, many=True)
        return Response(serializer.data)
