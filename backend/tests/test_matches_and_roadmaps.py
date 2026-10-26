import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User
from apps.resumes.models import Resume, ResumeSkill
from apps.jobs.models import Job, JobRequirement
from apps.matches.models import MatchResult
from apps.roadmaps.models import Roadmap

@pytest.mark.django_db
class TestMatchesAndRoadmaps:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='candidate@example.com', password='Password123!')
        self.client.force_authenticate(user=self.user)

        # Create candidate resume with Python and PostgreSQL
        self.resume = Resume.objects.create(
            owner=self.user,
            title="Candidate FullStack Resume",
            original_filename="resume.pdf",
            private_storage_key="user/resume.pdf",
            file_hash="hash_candidate",
            raw_text="Experienced engineer working with Python, Django, and PostgreSQL."
        )
        ResumeSkill.objects.create(resume=self.resume, skill_name='Python', evidence_text='Python microservices')
        ResumeSkill.objects.create(resume=self.resume, skill_name='PostgreSQL', evidence_text='PostgreSQL database tuning')

        # Create target job requiring Python, PostgreSQL, and Kubernetes
        self.job = Job.objects.create(
            owner=self.user,
            title="Platform Engineer",
            company_name="CloudScale",
            description="Looking for Platform Engineer. Required: Python, PostgreSQL, Kubernetes. Preferred: AWS."
        )
        JobRequirement.objects.create(job=self.job, skill_name='Python', is_mandatory=True, importance_weight=1.0)
        JobRequirement.objects.create(job=self.job, skill_name='PostgreSQL', is_mandatory=True, importance_weight=1.0)
        JobRequirement.objects.create(job=self.job, skill_name='Kubernetes', is_mandatory=True, importance_weight=1.0)
        JobRequirement.objects.create(job=self.job, skill_name='AWS', is_mandatory=False, importance_weight=0.5)

    def test_generate_match_and_breakdown(self):
        url = reverse('match-list-create')
        payload = {'resume_id': str(self.resume.id), 'job_id': str(self.job.id)}
        res = self.client.post(url, payload, format='json')

        assert res.status_code == 201
        data = res.data

        assert 'overall_score' in data
        assert data['overall_score'] > 0
        assert len(data['matched_skills']) >= 2 # Python and PostgreSQL
        assert any(s['skill_name'] == 'Kubernetes' for s in data['missing_skills'])

        match_id = data['id']

        # Test report export endpoint
        report_url = reverse('match-report-export', kwargs={'pk': match_id})
        report_res = self.client.get(report_url)
        assert report_res.status_code == 200
        assert b"SkillBridge Resume Intelligence Report" in report_res.content
        assert b"Platform Engineer" in report_res.content

    def test_generate_roadmap_and_toggle_completion(self):
        # First generate match
        match_url = reverse('match-list-create')
        match_res = self.client.post(match_url, {'resume_id': str(self.resume.id), 'job_id': str(self.job.id)}, format='json')
        match_id = match_res.data['id']

        # Generate roadmap
        roadmap_url = reverse('roadmap-list-create')
        roadmap_res = self.client.post(roadmap_url, {'match_id': match_id}, format='json')
        assert roadmap_res.status_code == 201
        roadmap_data = roadmap_res.data

        assert roadmap_data['total_items_count'] >= 1
        assert roadmap_data['completed_items_count'] == 0
        
        # Verify Kubernetes gap is prioritized
        k8s_item = next(item for item in roadmap_data['items'] if item['skill_name'] == 'Kubernetes')
        assert k8s_item['priority'] == 'HIGH'
        assert len(k8s_item['resources']) >= 1
        assert 'kubernetes.io' in k8s_item['resources'][0]['url']

        # Toggle completion
        item_id = k8s_item['id']
        toggle_url = reverse('roadmap-item-toggle', kwargs={'roadmap_id': roadmap_data['id'], 'item_id': item_id})
        toggle_res = self.client.patch(toggle_url, {'is_completed': True}, format='json')
        assert toggle_res.status_code == 200
        assert toggle_res.data['is_completed'] is True
        assert toggle_res.data['completed_at'] is not None
