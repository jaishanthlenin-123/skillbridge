import pytest
import io
from django.utils import timezone
from datetime import timedelta
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from apps.resumes.models import Resume
from apps.jobs.models import Job, JobRequirement
from apps.matches.models import MatchResult
from apps.roadmaps.models import Roadmap
from apps.accounts.guest import (
    create_guest_session, claim_guest_data_for_user,
    discard_guest_session, cleanup_expired_guest_sessions,
    GUEST_MAX_RESUMES
)

User = get_user_model()

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def mock_pdf_content():
    # Valid PDF header %PDF-1.4 with text content
    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /Resources <<>> /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Length 120 >>\nstream\n"
        b"BT\n/F1 12 Tf\n72 712 Td\n(Alex Rivera Senior Engineer Python Django React PostgreSQL Docker) Tj\nET\n"
        b"endstream\nendobj\nxref\n0 5\n"
        b"0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000216 00000 n \n"
        b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n386\n%%EOF\n"
    )

@pytest.fixture
def sample_job(db):
    job = Job.objects.create(
        title="Full Stack Engineer",
        company_name="Acme Tech",
        description="Looking for Python, Django, React, Docker skills.",
        is_sample=True
    )
    JobRequirement.objects.create(job=job, skill_name="Python", is_mandatory=True, importance_weight=1.0)
    JobRequirement.objects.create(job=job, skill_name="Django", is_mandatory=True, importance_weight=1.0)
    JobRequirement.objects.create(job=job, skill_name="React", is_mandatory=False, importance_weight=0.8)
    return job

@pytest.mark.django_db
class TestGuestWorkflow:

    def test_guest_session_creation(self, api_client):
        """Test GET /api/v1/auth/guest-session/ generates an isolated guest token."""
        resp = api_client.get('/api/v1/auth/guest-session/')
        assert resp.status_code == status.HTTP_201_CREATED
        assert 'token' in resp.data
        assert resp.data['is_guest'] is True
        assert 'user_id' in resp.data

        # Verify user was created in DB
        user = User.objects.get(id=resp.data['user_id'])
        assert user.email.endswith('@guest.skillbridge.local')

    def test_guest_session_reuse(self, api_client):
        """Test GET /api/v1/auth/guest-session/ with existing guest token reuses it."""
        resp1 = api_client.get('/api/v1/auth/guest-session/')
        token = resp1.data['token']

        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')
        resp2 = api_client.get('/api/v1/auth/guest-session/')
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data['token'] == token
        assert resp2.data['is_guest'] is True

    def test_guest_resume_upload_and_parse(self, api_client, mock_pdf_content):
        """Test guest can upload a resume and have skills extracted without an account."""
        guest_resp = api_client.get('/api/v1/auth/guest-session/')
        token = guest_resp.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "guest_alex_resume.pdf"

        upload_resp = api_client.post(
            '/api/v1/resumes/',
            {'file': pdf_file, 'title': 'Alex Rivera Resume'},
            format='multipart'
        )
        assert upload_resp.status_code == status.HTTP_201_CREATED
        resume_data = upload_resp.data
        assert resume_data['title'] == 'Alex Rivera Resume'
        assert resume_data['parsing_status'] == 'COMPLETED'
        assert len(resume_data['skills']) > 0

    def test_guest_data_isolation(self, api_client, mock_pdf_content):
        """Test Guest A cannot see or access Guest B's resumes."""
        # Guest A uploads a resume
        resp_a = api_client.get('/api/v1/auth/guest-session/')
        token_a = resp_a.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token_a}')

        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "resume_a.pdf"
        upload_a = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
        resume_a_id = upload_a.data['id']

        # Guest B initiates a separate guest session
        api_client.credentials()
        resp_b = api_client.get('/api/v1/auth/guest-session/')
        token_b = resp_b.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token_b}')

        # Guest B's resume list must be empty
        list_b = api_client.get('/api/v1/resumes/')
        assert list_b.status_code == status.HTTP_200_OK
        assert len(list_b.data) == 0

        # Guest B trying to access Guest A's resume directly must return 404
        detail_b = api_client.get(f'/api/v1/resumes/{resume_a_id}/')
        assert detail_b.status_code == status.HTTP_404_NOT_FOUND

    def test_guest_match_and_roadmap_end_to_end(self, api_client, mock_pdf_content, sample_job):
        """Test guest can analyze their resume against a job and generate a roadmap."""
        guest_resp = api_client.get('/api/v1/auth/guest-session/')
        token = guest_resp.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        # 1. Upload resume
        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "guest_engineer.pdf"
        upload = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
        resume_id = upload.data['id']

        # 2. Run match against sample job
        match_resp = api_client.post('/api/v1/matches/', {'resume_id': resume_id, 'job_id': str(sample_job.id)})
        assert match_resp.status_code == status.HTTP_201_CREATED
        match_id = match_resp.data['id']
        assert match_resp.data['overall_score'] > 0
        assert len(match_resp.data['matched_skills']) > 0

        # 3. View match detail
        detail_resp = api_client.get(f'/api/v1/matches/{match_id}/')
        assert detail_resp.status_code == status.HTTP_200_OK
        assert detail_resp.data['job_title'] == sample_job.title

        # 4. Generate learning roadmap
        roadmap_resp = api_client.post('/api/v1/roadmaps/', {'match_id': match_id})
        assert roadmap_resp.status_code == status.HTTP_201_CREATED
        roadmap_id = roadmap_resp.data['id']

        # 5. View roadmap detail
        roadmap_detail = api_client.get(f'/api/v1/roadmaps/{roadmap_id}/')
        assert roadmap_detail.status_code == status.HTTP_200_OK
        assert roadmap_detail.data['target_role'] == sample_job.title

    def test_guest_quota_enforcement(self, api_client, mock_pdf_content):
        """Test that guests cannot exceed the upload quota (max 3)."""
        guest_resp = api_client.get('/api/v1/auth/guest-session/')
        token = guest_resp.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        for i in range(GUEST_MAX_RESUMES):
            pdf_file = io.BytesIO(mock_pdf_content)
            pdf_file.name = f"resume_{i}.pdf"
            r = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
            assert r.status_code == status.HTTP_201_CREATED

        # 4th upload must be rejected with 400 Bad Request
        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "resume_overflow.pdf"
        overflow_resp = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
        assert overflow_resp.status_code == status.HTTP_400_BAD_REQUEST
        assert 'limit reached' in overflow_resp.data['error'].lower()

    def test_claim_guest_work_on_registration(self, api_client, mock_pdf_content, sample_job):
        """Test that registering an account seamlessly claims all guest uploads and matches."""
        guest_resp = api_client.get('/api/v1/auth/guest-session/')
        guest_token = guest_resp.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {guest_token}')

        # Upload resume and compute match as guest
        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "my_guest_resume.pdf"
        upload = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
        resume_id = upload.data['id']
        match = api_client.post('/api/v1/matches/', {'resume_id': resume_id, 'job_id': str(sample_job.id)})
        match_id = match.data['id']

        # Now register a permanent account
        api_client.credentials()  # Clear auth headers
        reg_resp = api_client.post(
            '/api/v1/auth/register/',
            {
                'email': 'new_candidate@skillbridge.test',
                'password': 'StrongPassword123!',
                'password_confirm': 'StrongPassword123!',
                'first_name': 'New',
                'last_name': 'Candidate',
                'guest_token': guest_token
            }
        )
        assert reg_resp.status_code == status.HTTP_201_CREATED
        new_token = reg_resp.data['token']
        assert reg_resp.data['claimed_guest_items'] >= 2

        # Verify new user owns the previously uploaded resume and match
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {new_token}')
        user_resumes = api_client.get('/api/v1/resumes/')
        assert len(user_resumes.data) == 1
        assert user_resumes.data[0]['id'] == resume_id

        user_matches = api_client.get('/api/v1/matches/')
        assert len(user_matches.data) == 1
        assert user_matches.data[0]['id'] == match_id

    def test_discard_guest_session(self, api_client, mock_pdf_content):
        """Test DELETE /api/v1/auth/guest-session/ discards temporary guest data and files."""
        guest_resp = api_client.get('/api/v1/auth/guest-session/')
        token = guest_resp.data['token']
        api_client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        pdf_file = io.BytesIO(mock_pdf_content)
        pdf_file.name = "temp_resume.pdf"
        upload = api_client.post('/api/v1/resumes/', {'file': pdf_file}, format='multipart')
        resume_id = upload.data['id']

        # Discard guest session
        del_resp = api_client.delete(
            '/api/v1/auth/guest-session/',
            headers={'X-Guest-Token': token}
        )
        assert del_resp.status_code == status.HTTP_200_OK
        assert del_resp.data['discarded'] is True

        # Resume record should be deleted
        assert not Resume.objects.filter(id=resume_id).exists()

    def test_cleanup_expired_guests_command(self, db):
        """Test cleanup utility deletes expired guest accounts and leaves registered accounts intact."""
        # Create a registered user
        registered_user = User.objects.create_user(email="permanent@example.com", password="pass")
        # Create an expired guest user (created 48 hours ago)
        expired_guest = User.objects.create_user(email="guest_old123@guest.skillbridge.local", password=None)
        expired_guest.created_at = timezone.now() - timedelta(hours=48)
        expired_guest.save()

        # Run cleanup
        count = cleanup_expired_guest_sessions(max_age_hours=24)
        assert count == 1
        assert not User.objects.filter(id=expired_guest.id).exists()
        assert User.objects.filter(id=registered_user.id).exists()
