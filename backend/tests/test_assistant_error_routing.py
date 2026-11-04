import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from apps.core.models import ErrorCode
from config.errors import ERROR_REGISTRY

@pytest.mark.django_db
class TestAssistantErrorRouting:
    def setup_method(self):
        self.client = APIClient()
        self.url = '/api/v1/assistant/chat/'

    @patch('apps.assistant.views.generate_assistant_response')
    def test_404_question_returns_predefined_response_without_gemini(self, mock_gemini):
        res = self.client.post(
            self.url,
            {'message': 'What does error 404 mean and what should I do?'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'predefined_error_registry'
        assert 'Error 404 — Page Not Found' in data['answer']
        assert "The page or resource you requested could not be found." in data['answer']
        assert "Check the URL for typing mistakes." in data['answer']
        assert "Return to the SkillBridge dashboard." in data['answer']
        # Gemini was NOT called!
        mock_gemini.assert_not_called()

    @patch('apps.assistant.views.generate_assistant_response')
    def test_500_question_returns_predefined_response_without_gemini(self, mock_gemini):
        res = self.client.post(
            self.url,
            {'message': 'What does error 500 mean and what should I do?'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'predefined_error_registry'
        assert 'Error 500 — Internal Server Error' in data['answer']
        assert "The SkillBridge server encountered an unexpected problem" in data['answer']
        assert "Refresh the page and try again." in data['answer']
        # Gemini was NOT called!
        mock_gemini.assert_not_called()

    @patch('apps.assistant.views.generate_assistant_response')
    def test_registered_error_sb_1001_bypasses_gemini(self, mock_gemini):
        res = self.client.post(
            self.url,
            {'message': 'What does error SB-1001 mean and what should I do?'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'predefined_error_registry'
        assert 'Error SB-1001' in data['answer']
        # Gemini was NOT called!
        mock_gemini.assert_not_called()

    @patch('apps.assistant.views.generate_assistant_response')
    def test_unknown_error_uses_gemini(self, mock_gemini):
        mock_gemini.return_value = {
            'answer': 'Error 999 is an uncataloged custom condition.',
            'mode': 'gemini_generated',
            'model': 'gemini-3.1-flash-lite',
            'can_create_ticket': True,
        }
        res = self.client.post(
            self.url,
            {'message': 'What does error 999 mean and what should I do?'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'gemini_generated'
        assert 'uncataloged' in data['answer']
        mock_gemini.assert_called_once()

    @patch('apps.assistant.views.generate_assistant_response')
    def test_general_error_question_uses_gemini(self, mock_gemini):
        mock_gemini.return_value = {
            'answer': 'I can assist you with general errors on the platform.',
            'mode': 'gemini_generated',
            'model': 'gemini-3.1-flash-lite',
            'can_create_ticket': False,
        }
        res = self.client.post(
            self.url,
            {'message': 'Can you help me understand this error and how to resolve it?'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'gemini_generated'
        mock_gemini.assert_called_once()

    @patch('apps.assistant.views.generate_assistant_response')
    def test_ordinary_question_with_numbers_does_not_trigger_error_route(self, mock_gemini):
        mock_gemini.return_value = {
            'answer': 'Working at Fortune 500 companies requires strong technical fundamentals.',
            'mode': 'gemini_generated',
            'model': 'gemini-3.1-flash-lite',
            'can_create_ticket': False,
        }
        res = self.client.post(
            self.url,
            {'message': 'Tell me about career strategies for Fortune 500 companies'},
            format='json'
        )
        assert res.status_code == 200
        data = res.json()
        assert data['mode'] == 'gemini_generated'
        mock_gemini.assert_called_once()
