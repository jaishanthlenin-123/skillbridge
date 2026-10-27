from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # SkillBridge API v1
    path('api/v1/', include('apps.core.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/resumes/', include('apps.resumes.urls')),
    path('api/v1/jobs/', include('apps.jobs.urls')),
    path('api/v1/matches/', include('apps.matches.urls')),
    path('api/v1/roadmaps/', include('apps.roadmaps.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/faq/', include('apps.faq.urls')),
    path('api/v1/support/', include('apps.support.urls')),
    path('api/v1/assistant/', include('apps.assistant.urls')),
    path('api/v1/integrations/', include('apps.integrations.urls')),

    # OpenAPI Schema & Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
