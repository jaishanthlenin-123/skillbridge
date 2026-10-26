import io
import pytest
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.resumes.models import Resume, ParsingStatus, Skill
from apps.resumes.seed_taxonomy import seed_skills_in_db
from apps.jobs.models import Job

@pytest.mark.django_db
class TestResumesAndJobs:
    def setup_method(self):
        seed_skills_in_db()
        self.client = APIClient()
        self.user = User.objects.create_user(email='engineer@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)

    def test_upload_invalid_extension(self):
        url = reverse('resume-list-create')
        bad_file = SimpleUploadedFile("malicious.exe", b"MZ\x90\x00\x03executable", content_type="application/octet-stream")
        res = self.client.post(url, {'file': bad_file}, format='multipart')
        assert res.status_code == 400
        assert 'error' in res.data or 'file' in res.data

    def test_upload_invalid_magic_bytes(self):
        url = reverse('resume-list-create')
        # Named .pdf but containing plain text or corrupted header
        corrupt_pdf = SimpleUploadedFile("fake.pdf", b"This is not a real PDF header", content_type="application/pdf")
        res = self.client.post(url, {'file': corrupt_pdf}, format='multipart')
        assert res.status_code == 400
        assert 'Invalid file signature' in str(res.data)

    def test_upload_valid_mock_pdf_and_parse(self, monkeypatch):
        # Generate a valid PDF stream in memory
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        text_content = """John Doe - Senior Software Engineer
Summary:
Results-driven engineer with expertise in scalable Python web services.
Experience:
Senior Developer at Acme Corp. Built microservices in Python, Django, and PostgreSQL.
Skills:
Python, React, TypeScript, Docker, PostgreSQL, REST APIs.
Education:
B.S. in Computer Science.
"""
        page.insert_text((50, 50), text_content)
        pdf_bytes = doc.tobytes()
        doc.close()

        uploaded_pdf = SimpleUploadedFile("resume.pdf", pdf_bytes, content_type="application/pdf")
        url = reverse('resume-list-create')
        res = self.client.post(url, {'file': uploaded_pdf, 'title': 'Software Engineer Resume'}, format='multipart')

        assert res.status_code == 201
        resume_id = res.data['id']
        assert res.data['parsing_status'] == ParsingStatus.COMPLETED

        # Check sections were parsed
        sections = res.data['sections']
        assert len(sections) >= 3

        # Check skills were extracted
        skills = [s['skill_name'] for s in res.data['skills']]
        assert 'Python' in skills
        assert 'PostgreSQL' in skills
        assert 'Docker' in skills

    def test_manual_skill_editing(self):
        resume = Resume.objects.create(
            owner=self.user,
            title="Dev Resume",
            original_filename="dev.pdf",
            private_storage_key="test/dev.pdf",
            file_hash="testhash123"
        )
        url = reverse('resume-skills-update', kwargs={'pk': resume.id})
        payload = {'skills': ['Python', 'Kubernetes', 'FastAPI']}
        res = self.client.post(url, payload, format='json')
        assert res.status_code == 200
        updated_skills = [s['skill_name'] for s in res.data['skills']]
        assert 'Kubernetes' in updated_skills
        assert 'FastAPI' in updated_skills

    def test_job_creation_and_requirement_extraction(self):
        url = reverse('job-list-create')
        payload = {
            'title': 'Senior Backend Engineer',
            'company_name': 'TechCorp',
            'description': 'Required: 5+ years of experience in Python and PostgreSQL. Must have experience with Docker. Nice to have: Kubernetes and AWS.'
        }
        res = self.client.post(url, payload, format='json')
        assert res.status_code == 201
        reqs = res.data['requirements']
        req_map = {r['skill_name']: r['is_mandatory'] for r in reqs}

        assert req_map.get('Python') is True
        assert req_map.get('PostgreSQL') is True
        assert req_map.get('Docker') is True
        assert req_map.get('Kubernetes') is False
        assert req_map.get('AWS') is False
