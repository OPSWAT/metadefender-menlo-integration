import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
import logging
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.sanitized_file_handler import SanitizedFileHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from fastapi import Request, Response
from fastapi.responses import StreamingResponse


class TestRetrieveSanitizedHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'timeout': {
                'sanitized': {
                    'enabled': False,
                    'value': 30
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        self.handler = SanitizedFileHandler(config=self.test_config)
        self.mock_request = MagicMock(spec=Request)
        self.mock_response = MagicMock(spec=Response)
        
        self.handler.meta_defender_api = Mock()
        self.handler.meta_defender_api.service_name = SERVICE.MetaDefenderCore
        self.handler.client_ip = '127.0.0.1'
        self.handler.apikey = 'test-api-key'
        
        self.original_logging_info = logging.info
        self.original_logging_error = logging.error
        logging.info = Mock()
        logging.error = Mock()

    def tearDown(self):
        logging.info = self.original_logging_info
        logging.error = self.original_logging_error

    def _setup_mock_request(self, uuid=None):
        self.mock_request.query_params = MagicMock()
        self.mock_request.query_params.get = Mock(return_value=uuid)
        self.mock_request.headers = MagicMock()
        self.mock_request.headers.get = Mock(side_effect=lambda key, default=None: {
            'Authorization': 'test-api-key',
            'X-Real-IP': '127.0.0.1'
        }.get(key, default))
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = '127.0.0.1'

    async def test_handle_get_success_stream(self):
        test_uuid = 'test-uuid-123'
        
        mock_resp = MagicMock()
        mock_resp.aiter_raw = MagicMock(return_value=iter([b'chunk1', b'chunk2']))
        mock_resp.headers = MagicMock()
        mock_resp.headers.get = MagicMock(side_effect=lambda key, default=None: {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="sanitized.pdf"'
        }.get(key, default))
        mock_resp.aclose = AsyncMock()
        
        mock_client = MagicMock()
        test_status = 200
        
        self._setup_mock_request(test_uuid)
        self.handler.meta_defender_api.sanitized_file = AsyncMock(
            return_value=(mock_resp, test_status, mock_client)
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertIsInstance(result, StreamingResponse)
        logging.info.assert_called()
        self.handler.meta_defender_api.sanitized_file.assert_called_once_with(
            test_uuid, 'test-api-key', '127.0.0.1'
        )

    async def test_handle_get_missing_uuid(self):
        self._setup_mock_request(None)
        result = await self.handler.handle_get(self.mock_request, self.mock_response)
        self.assertEqual(result, {'error': 'UUID parameter is required'})
        self.assertEqual(self.mock_response.status_code, 400)

    async def test_handle_get_non_200_status(self):
        test_uuid = 'test-uuid-456'
        
        mock_resp = MagicMock()
        mock_resp.aclose = AsyncMock()
        mock_client = MagicMock()
        test_status = 404
        
        self._setup_mock_request(test_uuid)
        self.handler.meta_defender_api.sanitized_file = AsyncMock(
            return_value=(mock_resp, test_status, mock_client)
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, test_status)
        mock_resp.aclose.assert_called_once()

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    async def test_handle_get_timeout(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        test_config_with_timeout = {
            'timeout': {
                'sanitized': {
                    'enabled': True,
                    'value': 0.1
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        handler = SanitizedFileHandler(config=test_config_with_timeout)
        handler.meta_defender_api = Mock()
        handler.meta_defender_api.service_name = SERVICE.MetaDefenderCore
        
        test_uuid = 'test-uuid-timeout'
        self._setup_mock_request(test_uuid)
        
        async def slow_sanitized_file(*args):
            await asyncio.sleep(1)
            return (MagicMock(), 200, MagicMock())
        
        handler.meta_defender_api.sanitized_file = slow_sanitized_file
        
        result = await handler.handle_get(self.mock_request, self.mock_response)
        
        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called()

    async def test_handle_get_general_error(self):
        test_uuid = 'test-uuid-error'
        self._setup_mock_request(test_uuid)
        self.handler.meta_defender_api.sanitized_file = AsyncMock(
            side_effect=Exception('API error')
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called()


if __name__ == '__main__':
    unittest.main()
