import pytest
from unittest.mock import patch, MagicMock
from rest_framework import status
import requests

from apps.assistant.chains import generate_assistant_response
from apps.assistant.faq_retriever import retrieve_relevant_faqs
from apps.support.models import SupportTicket

@pytest.mark.django_db
class TestGeminiAssistantRegression:

    def mock_gemini_success(self, text: str):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'candidates': [
                {'content': {'parts': [{'text': text}]}}
            ]
        }
        return mock_resp

    @patch('apps.assistant.chains.requests.post')
    def test_hi_how_are_you_calls_gemini(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success("Hello! I'm doing great. How can I help with your career?")

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Hi, how are you?'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "doing great" in data['answer']
        assert mock_post.called

    @patch('apps.assistant.chains.requests.post')
    def test_user_intro_career_calls_gemini(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success("Welcome Jaishanth! To become an ML engineer, focus on Python and PyTorch.")

        resp = client.post(
            '/api/v1/assistant/chat/',
            {'message': 'My name is Jaishanth. I want to become a machine learning engineer.'},
            format='json'
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "Welcome Jaishanth" in data['answer']
        assert mock_post.called

    @patch('apps.assistant.chains.requests.post')
    def test_how_do_i_get_a_learning_roadmap_calls_gemini(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success(
            "To get a learning roadmap on SkillBridge, first upload your resume and run a match analysis against a job."
        )

        resp = client.post('/api/v1/assistant/chat/', {'message': 'How do I get a learning roadmap?'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "learning roadmap" in data['answer']
        assert mock_post.called

    @patch('apps.assistant.chains.requests.post')
    def test_explain_gradient_descent_calls_gemini(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success(
            "Gradient descent is an optimization algorithm used to minimize a loss function by iteratively moving in the direction of steepest descent."
        )

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Explain gradient descent with an example.'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "optimization algorithm" in data['answer']

    @patch('apps.assistant.chains.requests.post')
    def test_supervised_vs_unsupervised_calls_gemini(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success(
            "Supervised learning trains on labeled data, while unsupervised learning discovers hidden patterns in unlabeled data."
        )

        resp = client.post(
            '/api/v1/assistant/chat/',
            {'message': 'What is the difference between supervised and unsupervised learning?'},
            format='json'
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "labeled data" in data['answer']

    @patch('apps.assistant.chains.requests.post')
    def test_skillbridge_faq_question_provides_context(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success(
            "To upload your resume on SkillBridge, simply visit the Resume tab and drag and drop your PDF or DOCX file."
        )

        resp = client.post('/api/v1/assistant/chat/', {'message': 'How do I upload a resume on SkillBridge?'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        # Ensure Gemini received the payload with documentation
        sent_payload = mock_post.call_args[1]['json']
        system_instruction = sent_payload['system_instruction']['parts'][0]['text']
        assert "SkillBridge" in system_instruction

    @patch('apps.assistant.chains.requests.post')
    def test_general_question_without_faqs(self, mock_post, client):
        mock_post.return_value = self.mock_gemini_success("Quantum computing utilizes superposition and entanglement.")

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Explain quantum superposition.'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'gemini_generated'
        assert "Quantum computing" in data['answer']

    @patch('apps.assistant.chains.requests.post')
    def test_gemini_429_quota_exhaustion_returns_honest_error(self, mock_post, client):
        mock_429 = MagicMock()
        mock_429.status_code = 429
        mock_429.text = '{"error": {"code": 429, "message": "Resource exhausted"}}'
        mock_post.return_value = mock_429

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Can you evaluate my resume?'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'service_unavailable'
        assert "Quota Exceeded" in data['answer'] or "429" in data['answer']
        assert data['can_create_ticket'] is True

    @patch('apps.assistant.chains.requests.post')
    def test_gemini_503_overload_returns_service_unavailable(self, mock_post, client):
        mock_503 = MagicMock()
        mock_503.status_code = 503
        mock_503.text = '{"error": {"code": 503, "message": "High demand"}}'
        mock_post.return_value = mock_503

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Tell me about career roadmaps.'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'service_unavailable'
        assert "503" in data['answer'] or "Overloaded" in data['answer']

    @patch('apps.assistant.chains.requests.post')
    def test_gemini_timeout_returns_clear_error(self, mock_post, client):
        mock_post.side_effect = requests.exceptions.ReadTimeout("Read timed out")

        resp = client.post('/api/v1/assistant/chat/', {'message': 'Deep learning algorithms'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'service_unavailable'
        assert "Timed Out" in data['answer']

    @patch('apps.assistant.chains.requests.post')
    def test_gemini_empty_json_candidates_handled(self, mock_post, client):
        mock_empty = MagicMock()
        mock_empty.status_code = 200
        mock_empty.json.return_value = {'candidates': []}
        mock_post.return_value = mock_empty

        resp = client.post('/api/v1/assistant/chat/', {'message': 'What is AI?'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'service_unavailable'

    @patch.dict('os.environ', {'GEMINI_API_KEY': ''}, clear=False)
    def test_missing_api_key_reports_configuration_problem(self, client):
        resp = client.post('/api/v1/assistant/chat/', {'message': 'Hello'}, format='json')
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data['mode'] == 'service_unavailable'
        assert "GEMINI_API_KEY" in data['answer']

    def test_explicit_support_ticket_creation(self, client):
        resp = client.post(
            '/api/v1/assistant/chat/',
            {
                'action': 'create_ticket',
                'message': 'Cannot upload my resume, getting error',
                'email': 'tester@example.com',
                'subject': 'Resume Upload Assistance'
            },
            format='json'
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data['ticket_created'] is True
        assert data['ticket_number'].startswith('SB-')
        assert SupportTicket.objects.filter(ticket_number=data['ticket_number']).exists()
