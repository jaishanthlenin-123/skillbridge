import pytest
from django.test import Client
from core.models import ErrorCode

@pytest.mark.django_db
class TestDjangoTemplates:
    def setup_method(self):
        self.client = Client()

    def test_home_page_rendered_with_django_template(self):
        response = self.client.get('/')
        assert response.status_code == 200
        assert 'home.html' in [t.name for t in response.templates]
        assert 'base.html' in [t.name for t in response.templates]

        content = response.content.decode('utf-8')
        assert 'SkillBridge Backend & API Services' in content
        assert 'Django Templates (DTL)' in content
        assert 'Swagger API Docs' in content
        assert 'Error Registry' in content

    def test_error_registry_page_rendered_with_django_template(self):
        response = self.client.get('/portal/errors/')
        assert response.status_code == 200
        assert 'error_registry.html' in [t.name for t in response.templates]
        assert 'base.html' in [t.name for t in response.templates]

        content = response.content.decode('utf-8')
        assert 'Standardized Platform Error Codes' in content
        assert '404' in content
        assert '500' in content
        assert 'SB-1001' in content
        assert 'HTTP 404' in content
        assert 'HTTP 500' in content

    def test_template_context_data(self):
        response = self.client.get('/')
        assert response.status_code == 200
        assert 'error_count' in response.context
        assert response.context['error_count'] > 0
        assert 'frontend_url' in response.context

