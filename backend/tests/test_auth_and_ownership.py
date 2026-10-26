import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.resumes.models import Resume
from apps.jobs.models import Job

@pytest.mark.django_db
class TestAuthenticationAndOwnership:
    def setup_method(self):
        self.client = APIClient()
        self.user_a = User.objects.create_user(email='user_a@example.com', password='Password123!', first_name='Alice')
        self.user_b = User.objects.create_user(email='user_b@example.com', password='Password123!', first_name='Bob')

    def test_user_registration_success(self):
        url = reverse('auth-register')
        payload = {
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'StrongPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        res = self.client.post(url, payload)
        assert res.status_code == 201
        assert 'token' in res.data
        assert res.data['user']['email'] == 'newuser@example.com'

    def test_user_registration_password_mismatch(self):
        url = reverse('auth-register')
        payload = {
            'email': 'mismatch@example.com',
            'password': 'StrongPassword123!',
            'password_confirm': 'DifferentPassword123!',
        }
        res = self.client.post(url, payload)
        assert res.status_code == 400
        assert 'password_confirm' in res.data

    def test_user_login_success(self):
        url = reverse('auth-login')
        payload = {'email': 'user_a@example.com', 'password': 'Password123!'}
        res = self.client.post(url, payload)
        assert res.status_code == 200
        assert 'token' in res.data
        assert res.data['user']['id'] == str(self.user_a.id)

    def test_user_login_invalid_credentials(self):
        url = reverse('auth-login')
        payload = {'email': 'user_a@example.com', 'password': 'WrongPassword!'}
        res = self.client.post(url, payload)
        assert res.status_code == 400

    def test_cross_user_isolation_resume(self):
        """User A must NOT be able to view, patch, or delete User B's resume."""
        resume_b = Resume.objects.create(
            owner=self.user_b,
            title="Bob's Private Resume",
            original_filename="bob_resume.pdf",
            private_storage_key="user_b/dummy.pdf",
            file_hash="dummyhashb"
        )

        # Authenticate as User A
        self.client.force_authenticate(user=self.user_a)

        # Attempt to GET Bob's resume
        detail_url = reverse('resume-detail', kwargs={'pk': resume_b.id})
        res_get = self.client.get(detail_url)
        assert res_get.status_code == 404

        # Attempt to PATCH Bob's resume
        res_patch = self.client.patch(detail_url, {'title': 'Hacked Title'})
        assert res_patch.status_code == 404

        # Attempt to DELETE Bob's resume
        res_delete = self.client.delete(detail_url)
        assert res_delete.status_code == 404
        assert Resume.objects.filter(id=resume_b.id).exists()

    def test_cross_user_isolation_job(self):
        """User A must NOT be able to view, patch, or delete User B's job."""
        job_b = Job.objects.create(
            owner=self.user_b,
            title="Bob's Confidential Tech Lead Role",
            description="High priority confidential role"
        )

        self.client.force_authenticate(user=self.user_a)

        detail_url = reverse('job-detail', kwargs={'pk': job_b.id})
        res_get = self.client.get(detail_url)
        assert res_get.status_code == 404

        res_delete = self.client.delete(detail_url)
        assert res_delete.status_code == 404
        assert Job.objects.filter(id=job_b.id).exists()
