import os
import time
import requests
from unittest.mock import patch, MagicMock
from django.test import SimpleTestCase

from apps.assistant.model_router import (
    route_model_request,
    reset_model_router_state,
    set_model_cooldown,
    is_model_in_cooldown,
    get_configured_models
)

class ModelRouterResilienceTests(SimpleTestCase):
    def setUp(self):
        reset_model_router_state()
        self.patcher_key = patch.dict(os.environ, {
            'GEMINI_API_KEY': 'test-dummy-api-key',
            'GEMINI_PRIMARY_MODEL': 'gemini-3.1-flash-lite',
            'GEMINI_FALLBACK_MODELS': 'gemini-3.5-flash-lite,gemini-flash-lite-latest'
        })
        self.patcher_key.start()

    def tearDown(self):
        self.patcher_key.stop()
        reset_model_router_state()

    def test_configured_models_resolution(self):
        primary, fallbacks = get_configured_models()
        self.assertEqual(primary, 'gemini-3.1-flash-lite')
        self.assertEqual(fallbacks, ['gemini-3.5-flash-lite', 'gemini-flash-lite-latest'])

    @patch('requests.post')
    def test_primary_model_succeeds(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Hello from gemini-3.1-flash-lite!'}]}}]
        }
        mock_post.return_value = mock_resp

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Hello'}]}]}
        res = route_model_request(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.model_used, 'gemini-3.1-flash-lite')
        self.assertEqual(res.mode, 'gemini_generated')
        self.assertEqual(res.attempts, 1)
        self.assertIn('gemini-3.1-flash-lite', res.answer)

    @patch('requests.post')
    def test_primary_quota_exceeded_fails_over_to_fallback(self, mock_post):
        # 1st attempt: gemini-3.1-flash-lite returns 429
        # 2nd attempt: gemini-3.5-flash-lite returns 200
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.json.return_value = {'error': {'code': 429, 'message': 'Resource exhausted'}}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Hello from fallback gemini-3.5-flash-lite!'}]}}]
        }

        mock_post.side_effect = [resp_429, resp_200]

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Hello'}]}]}
        res = route_model_request(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.model_used, 'gemini-3.5-flash-lite')
        self.assertEqual(res.attempts, 2)
        self.assertIn('gemini-3.5-flash-lite', res.answer)

        # Primary model must be placed in cooldown
        self.assertTrue(is_model_in_cooldown('gemini-3.1-flash-lite'))

    @patch('requests.post')
    def test_primary_timeout_fails_over_to_fallback(self, mock_post):
        # 1st attempt: Timeout
        # 2nd attempt: 200 OK on fallback
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Fallback answer after timeout.'}]}}]
        }

        mock_post.side_effect = [requests.exceptions.Timeout('Connection timeout'), resp_200]

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Test'}]}]}
        res = route_model_request(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.model_used, 'gemini-3.5-flash-lite')
        self.assertEqual(res.attempts, 2)

    @patch('requests.post')
    def test_primary_503_high_demand_fails_over(self, mock_post):
        resp_503 = MagicMock()
        resp_503.status_code = 503
        resp_503.json.return_value = {'error': {'code': 503, 'message': 'High demand'}}

        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Recovered via fallback.'}]}}]
        }

        mock_post.side_effect = [resp_503, resp_200]

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Test'}]}]}
        res = route_model_request(payload)

        self.assertTrue(res.success)
        self.assertEqual(res.model_used, 'gemini-3.5-flash-lite')
        self.assertTrue(is_model_in_cooldown('gemini-3.1-flash-lite'))

    @patch('requests.post')
    def test_model_in_cooldown_is_skipped(self, mock_post):
        # Put gemini-3.1-flash-lite in cooldown
        set_model_cooldown('gemini-3.1-flash-lite', 60.0)

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            'candidates': [{'content': {'parts': [{'text': 'Direct from fallback!'}]}}]
        }
        mock_post.return_value = mock_resp

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Test'}]}]}
        res = route_model_request(payload)

        # Should immediately use the fallback without calling primary
        self.assertTrue(res.success)
        self.assertEqual(res.model_used, 'gemini-3.5-flash-lite')
        self.assertEqual(res.attempts, 1)

    @patch('requests.post')
    def test_invalid_credentials_does_not_failover_endlessly(self, mock_post):
        resp_401 = MagicMock()
        resp_401.status_code = 401
        resp_401.json.return_value = {'error': {'code': 401, 'message': 'API key not valid'}}
        mock_post.return_value = resp_401

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Test'}]}]}
        res = route_model_request(payload)

        self.assertFalse(res.success)
        self.assertEqual(res.attempts, 1)
        self.assertEqual(res.error_category, 'AUTH_ERROR_401')
        self.assertIn('Authorization Error', res.answer)

    @patch('requests.post')
    def test_all_models_fail_returns_transparent_unavailability(self, mock_post):
        resp_429 = MagicMock()
        resp_429.status_code = 429
        resp_429.json.return_value = {'error': {'code': 429, 'message': 'Resource exhausted'}}
        mock_post.return_value = resp_429

        payload = {'contents': [{'role': 'user', 'parts': [{'text': 'Test'}]}]}
        res = route_model_request(payload)

        self.assertFalse(res.success)
        self.assertEqual(res.mode, 'service_unavailable')
        self.assertEqual(res.attempts, 3) # primary + 2 fallbacks
        self.assertIn('Quota Exceeded', res.answer)
        self.assertTrue(res.can_create_ticket)
