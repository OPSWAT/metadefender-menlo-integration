import logging
import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.check_handler import CheckHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from fastapi import Request, Response


class TestCheckExistingHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'timeout': {
                'check': {
                    'enabled': False,
                    'value': 30
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        self.handler = CheckHandler(config=self.test_config)
        self.mock_request = MagicMock(spec=Request)
        self.mock_response = MagicMock(spec=Response)
        
        self.handler.meta_defender_api = Mock()
        self.handler.meta_defender_api.service_name = SERVICE.meta_defender_core
        self.handler.client_ip = '127.0.0.1'
        self.handler.apikey = 'test-api-key'

        self.original_logging_info = logging.info
        self.original_logging_error = logging.error
        logging.info = Mock()
        logging.error = Mock()

    def tearDown(self):
        logging.info = self.original_logging_info
        logging.error = self.original_logging_error

    def _setup_mock_request(self, sha256=None):
        self.mock_request.query_params = MagicMock()
        self.mock_request.query_params.get = Mock(return_value=sha256)
        self.mock_request.headers = MagicMock()
        self.mock_request.headers.get = Mock(side_effect=lambda key, default=None: {
            'Authorization': 'test-api-key',
            'X-Real-IP': '127.0.0.1'
        }.get(key, default))
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = '127.0.0.1'

    @patch('metadefender_menlo.api.handlers.check_handler.CheckExisting')
    async def test_handle_get_success(self, mock_check_existing):
        test_sha256 = 'a' * 64
        initial_response = {
            'scan_results': {'scan_all_result_i': 0},
            'file_info': {'file_size': 1024}
        }
        expected_response = {
            'result': 'clean',
            'sha256': test_sha256
        }

        self._setup_mock_request(test_sha256)
        self.handler.meta_defender_api.check_hash = AsyncMock(
            return_value=(initial_response, 200)
        )

        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response = AsyncMock(
            return_value=(expected_response, 200)
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, expected_response)
        self.assertEqual(self.mock_response.status_code, 200)
        logging.info.assert_called()
        self.handler.meta_defender_api.check_hash.assert_called_once_with(
            test_sha256, 'test-api-key', '127.0.0.1'
        )

    async def test_handle_get_missing_sha256(self):
        self._setup_mock_request(None)
        result = await self.handler.handle_get(self.mock_request, self.mock_response)
        self.assertEqual(result, {'error': 'SHA256 parameter is required'})
        self.assertEqual(self.mock_response.status_code, 400)

    @patch('metadefender_menlo.api.handlers.check_handler.CheckExisting')
    async def test_handle_get_api_error(self, mock_check_existing):
        test_sha256 = 'b' * 64
        test_error = Exception("API connection error")

        self._setup_mock_request(test_sha256)
        self.handler.meta_defender_api.check_hash = AsyncMock(side_effect=test_error)

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    @patch('metadefender_menlo.api.handlers.check_handler.CheckExisting')
    async def test_handle_get_with_timeout_enabled(self, mock_check_existing, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        test_config_with_timeout = {
            'timeout': {
                'check': {
                    'enabled': True,
                    'value': 5
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        handler = CheckHandler(config=test_config_with_timeout)
        handler.meta_defender_api = Mock()
        handler.meta_defender_api.service_name = SERVICE.meta_defender_core
        
        test_sha256 = 'c' * 64
        expected_response = {'result': 'clean'}
        
        self._setup_mock_request(test_sha256)
        
        handler.meta_defender_api.check_hash = AsyncMock(
            return_value=({'result': 'clean'}, 200)
        )
        
        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response = AsyncMock(
            return_value=(expected_response, 200)
        )
        
        self.assertEqual(handler.handler_timeout, 5)
        
        result = await handler.handle_get(self.mock_request, self.mock_response)
        
        self.assertEqual(result, expected_response)


if __name__ == '__main__':
    unittest.main()
