import unittest
from unittest.mock import Mock, MagicMock, patch
import logging

import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.health_handler import HealthHandler
from fastapi import Request, Response


class TestHealthCheckHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'commitHash': 'abc123',
            'scanRule': 'test-rule',
            'allowlist': {
                'enabled': False
            }
        }

        self.handler = HealthHandler(config=self.test_config)
        
        self.mock_request = MagicMock(spec=Request)
        self.mock_response = MagicMock(spec=Response)
        
        self.original_logging_debug = logging.debug
        logging.debug = Mock()

    def tearDown(self):
        logging.debug = self.original_logging_debug

    async def test_handle_request(self):
        expected_response = {
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "2.0.2",
            "commitHash": self.test_config['commitHash'],
            "rule": self.test_config['scanRule']
        }

        result = await self.handler.handle_request(self.mock_request, self.mock_response)

        self.assertEqual(result, expected_response)
        self.assertIn('status', result)
        self.assertIn('name', result)
        self.assertIn('version', result)
        self.assertIn('commitHash', result)
        self.assertIn('rule', result)

    async def test_handle_request_response_format(self):
        result = await self.handler.handle_request(self.mock_request, self.mock_response)

        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'Ready')
        self.assertEqual(result['name'], 'MetaDefender - Menlo integration')
        self.assertEqual(result['version'], '2.0.2')
        self.assertEqual(result['commitHash'], self.test_config['commitHash'])
        self.assertEqual(result['rule'], self.test_config['scanRule'])

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    async def test_handle_request_with_different_config(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        different_config = {
            'commitHash': 'xyz789',
            'scanRule': 'different-rule',
            'allowlist': {
                'enabled': False
            }
        }
        
        handler = HealthHandler(config=different_config)
        result = await handler.handle_request(self.mock_request, self.mock_response)

        self.assertEqual(result['commitHash'], 'xyz789')
        self.assertEqual(result['rule'], 'different-rule')

    async def test_handle_request_returns_dict(self):
        result = await self.handler.handle_request(self.mock_request, self.mock_response)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(len(result), 5)


if __name__ == '__main__':
    unittest.main()
