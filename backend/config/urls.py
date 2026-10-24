from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from core.views import PortalHomeView, PortalErrorRegistryView

urlpatterns = [
    # Django Template Portal Views
    path('', PortalHomeView.as_view(), name='portal-home'),
    path('portal/errors/', PortalErrorRegistryView.as_view(), name='portal-errors'),

    path('admin/', admin.site.urls),

    # SkillBridge API v1
    path('api/v1/', include('core.urls')),
    path('api/v1/auth/', include('accounts.urls')),
    path('api/v1/resumes/', include('resumes.urls')),
    path('api/v1/jobs/', include('jobs.urls')),
    path('api/v1/matches/', include('matches.urls')),
    path('api/v1/roadmaps/', include('roadmaps.urls')),
    path('api/v1/audit/', include('audit.urls')),
    path('api/v1/faq/', include('faq.urls')),
    path('api/v1/support/', include('support.urls')),
    path('api/v1/assistant/', include('assistant.urls')),
    path('api/v1/integrations/', include('integrations.urls')),

    # OpenAPI Schema & Swagger Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
