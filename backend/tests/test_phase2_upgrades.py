import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.management import call_command

from apps.faq.models import FAQ, FAQCategory
from apps.support.models import SupportTicket
from apps.jobs.models import Job
from apps.resumes.models import Resume, Skill, ResumeSkill
from apps.matches.models import MatchResult

User = get_user_model()

@pytest.mark.django_db
class TestPhase2SkillBridgeUpgrades:

    @pytest.fixture(autouse=True)
    def setup_data(self):
        call_command('seed_skillbridge')
        self.user = User.objects.create_user(
            email='alice_test@example.com',
            password='Password123!',
            first_name='Alice'
        )

    # 1. Database & Seed Verification
    def test_seeded_faqs_count_minimum_ten(self):
        faq_count = FAQ.objects.filter(is_active=True).count()
        assert faq_count >= 10, f"Expected at least 10 FAQs, found {faq_count}"

    def test_seeded_sample_jobs_exist(self):
        sample_jobs = Job.objects.filter(is_sample=True)
        assert sample_jobs.count() >= 4
        first_job = sample_jobs.first()
        assert first_job.requirements.count() > 0

    # 2. FAQ API Tests
    def test_faq_list_and_search(self, client):
        resp = client.get('/api/v1/faq/')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) >= 10

        # Search query for "upload"
        search_resp = client.get('/api/v1/faq/?q=upload')
        assert search_resp.status_code == status.HTTP_200_OK
        search_data = search_resp.json()
        assert len(search_data) >= 1
        assert any('upload' in item['question'].lower() or 'upload' in item['answer'].lower() for item in search_data)

    # 3. Support Tickets API Tests
    def test_support_ticket_creation_guest_and_user(self, client):
        # Guest submission requires contact_email
        fail_resp = client.post('/api/v1/support/', {
            'subject': 'Help needed',
            'description': 'My file will not parse',
        }, content_type='application/json')
        assert fail_resp.status_code == status.HTTP_400_BAD_REQUEST

        # Valid guest submission
        guest_resp = client.post('/api/v1/support/', {
            'contact_email': 'guest_user@example.com',
            'subject': 'Help with parsing',
            'description': 'My PDF file is not uploading',
            'category': 'parsing',
        }, content_type='application/json')
        assert guest_resp.status_code == status.HTTP_201_CREATED
        guest_ticket = guest_resp.json()
        assert guest_ticket['ticket_number'].startswith('SB-')

        # Lookup guest ticket
        lookup_resp = client.get(
            f"/api/v1/support/lookup/?ticket_number={guest_ticket['ticket_number']}&email=guest_user@example.com"
        )
        assert lookup_resp.status_code == status.HTTP_200_OK

        # Authenticated submission
        client.force_login(self.user)
        auth_resp = client.post('/api/v1/support/', {
            'subject': 'User question',
            'description': 'Detailed question from logged in user',
        }, content_type='application/json')
        assert auth_resp.status_code == status.HTTP_201_CREATED
        auth_data = auth_resp.json()
        assert auth_data['contact_email'] == self.user.email

    # 4. Error Registry & Middleware Tests
    def test_error_registry_and_request_id_middleware(self, client):
        resp = client.get('/api/v1/errors/')
        assert resp.status_code == status.HTTP_200_OK
        assert 'X-Request-ID' in resp.headers
        data = resp.json()
        assert data['count'] >= 8
        error_codes = [e['code'] for e in data['errors']]
        for code in ['400', '401', '403', '404', '429', '500', '503', 'SB-1001']:
            assert code in error_codes

        # Lookup specific error code
        code_resp = client.get('/api/v1/errors/SB-1001/')
        assert code_resp.status_code == status.HTTP_200_OK
        code_data = code_resp.json()
        assert code_data['code'] == 'SB-1001'
        assert 'Resume Processing Failed' in code_data['title']

    # 5. Health and Readiness Tests
    def test_health_and_readiness_endpoints(self, client):
        health_resp = client.get('/api/v1/health/')
        assert health_resp.status_code == status.HTTP_200_OK
        assert health_resp.json()['status'] == 'healthy'

        readiness_resp = client.get('/api/v1/readiness/')
        assert readiness_resp.status_code == status.HTTP_200_OK
        r_data = readiness_resp.json()
        assert r_data['ready'] is True
        assert r_data['checks']['database']['status'] == 'up'

    # 6. AI Assistant Chat & Escalation Tests
    @patch('apps.assistant.chains.requests.post')
    def test_assistant_chat_error_explanation(self, mock_post, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'candidates': [
                {'content': {'parts': [{'text': 'Error SB-1001 means Resume Processing Failed. We were unable to extract text.'}]}}
            ]
        }
        mock_post.return_value = mock_resp

        resp = client.post('/api/v1/assistant/chat/', {
            'message': 'What does error SB-1001 mean?',
            'conversation_id': 'test_conv_123',
        }, content_type='application/json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert 'SB-1001' in data['answer']
        assert 'Resume Processing Failed' in data['answer'] or 'extract' in data['answer'].lower()

    def test_assistant_chat_ticket_creation(self, client):
        resp = client.post('/api/v1/assistant/chat/', {
            'action': 'create_ticket',
            'message': 'I need human help with matching scores',
            'email': 'escalate@example.com',
            'conversation_id': 'test_conv_escalate',
        }, content_type='application/json')
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data['ticket_created'] is True
        assert data['ticket_number'].startswith('SB-')
        # Verify ticket persisted in PostgreSQL
        assert SupportTicket.objects.filter(ticket_number=data['ticket_number']).exists()

    def test_assistant_feedback_submission(self, client):
        resp = client.post('/api/v1/assistant/feedback/', {
            'conversation_id': 'test_conv_fb',
            'rating': 5,
            'comment': 'Extremely helpful assistant!'
        }, content_type='application/json')
        assert resp.status_code == status.HTTP_200_OK

    # 7. GitHub Integration API Test
    @patch('apps.integrations.github.requests.get')
    def test_github_profile_insights(self, mock_get, client):
        mock_user_resp = MagicMock()
        mock_user_resp.status_code = 200
        mock_user_resp.json.return_value = {
            'login': 'octocat',
            'name': 'The Octocat',
            'bio': 'Developer',
            'public_repos': 8,
            'avatar_url': 'https://example.com/avatar.png'
        }

        mock_repos_resp = MagicMock()
        mock_repos_resp.status_code = 200
        mock_repos_resp.json.return_value = [
            {
                'name': 'awesome-python',
                'language': 'Python',
                'topics': ['machine-learning', 'django'],
                'stargazers_count': 42,
                'fork': False,
                'html_url': 'https://github.com/octocat/awesome-python'
            }
        ]

        mock_get.side_effect = [mock_user_resp, mock_repos_resp]

        resp = client.get('/api/v1/integrations/github/?username=octocat')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['status'] == 'success'
        assert data['username'] == 'octocat'
        assert 'Python' in data['top_languages']

    # 8. Sample Job Accessibility and Match Analysis
    def test_sample_jobs_visible_and_matchable(self, client):
        # 1. Guest can list sample jobs
        guest_resp = client.get('/api/v1/jobs/')
        assert guest_resp.status_code == status.HTTP_200_OK
        jobs = guest_resp.json()
        assert len(jobs) >= 4
        sample_job = jobs[0]
        assert sample_job['is_sample'] is True

        # 2. Authenticated user can run match against this sample job
        client.force_login(self.user)
        resume = Resume.objects.create(
            owner=self.user,
            title='Alice Tech Resume',
            original_filename='alice_resume.pdf',
            private_storage_key='resumes/test_alice.pdf',
            file_hash='fakehash1234567890abcdef',
            file_size_bytes=1024,
            raw_text='Experienced Python and React developer building cloud apps with Docker and PostgreSQL.',
            parsing_status='COMPLETED'
        )
        skill_python = Skill.objects.get(name='Python')
        ResumeSkill.objects.create(
            resume=resume,
            skill=skill_python,
            skill_name='Python',
            confidence=0.95
        )

        match_resp = client.post('/api/v1/matches/', {
            'resume_id': str(resume.id),
            'job_id': sample_job['id']
        }, content_type='application/json')
        assert match_resp.status_code == status.HTTP_201_CREATED
        match_data = match_resp.json()
        assert match_data['overall_score'] >= 0.0
        assert MatchResult.objects.filter(id=match_data['id']).exists()
