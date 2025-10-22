import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import asyncio
import logging
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.result_handler import ResultHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from fastapi import Request, Response


class TestAnalysisResultHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'timeout': {
                'result': {
                    'enabled': False,
                    'value': 30
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        self.handler = ResultHandler(config=self.test_config)
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

    @patch('metadefender_menlo.api.handlers.result_handler.FileAnalyis')
    async def test_handle_get_success(self, mock_file_analysis):
        test_uuid = 'test-uuid-123'
        test_response = {
            'result': 'completed',
            'outcome': 'clean',
            'report_url': 'http://example.com/report'
        }
        test_status = 200

        self._setup_mock_request(test_uuid)
        self.handler.meta_defender_api.check_result = AsyncMock(
            return_value=(test_response, test_status)
        )

        mock_file_analysis_instance = mock_file_analysis.return_value
        mock_file_analysis_instance.handle_response = AsyncMock(
            return_value=(test_response, test_status)
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, test_response)
        self.assertEqual(self.mock_response.status_code, test_status)
        logging.info.assert_called()
        self.handler.meta_defender_api.check_result.assert_called_once_with(
            test_uuid, 'test-api-key', '127.0.0.1'
        )
        mock_file_analysis_instance.handle_response.assert_called_once_with(
            test_response, test_status
        )

    async def test_handle_get_missing_uuid(self):
        self._setup_mock_request(None)
        result = await self.handler.handle_get(self.mock_request, self.mock_response)
        self.assertEqual(result, {'error': 'UUID parameter is required'})
        self.assertEqual(self.mock_response.status_code, 400)

    @patch('metadefender_menlo.api.handlers.result_handler.FileAnalyis')
    async def test_handle_get_api_error(self, mock_file_analysis):
        test_uuid = 'test-uuid-456'
        self._setup_mock_request(test_uuid)
        self.handler.meta_defender_api.check_result = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await self.handler.handle_get(self.mock_request, self.mock_response)

        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    @patch('metadefender_menlo.api.handlers.result_handler.FileAnalyis')
    async def test_handle_get_timeout(self, mock_file_analysis, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        test_config_with_timeout = {
            'timeout': {
                'result': {
                    'enabled': True,
                    'value': 0.1
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        handler = ResultHandler(config=test_config_with_timeout)
        handler.meta_defender_api = Mock()
        handler.meta_defender_api.service_name = SERVICE.MetaDefenderCore
        
        test_uuid = 'test-uuid-timeout'
        self._setup_mock_request(test_uuid)
        
        async def slow_check_result(*args):
            await asyncio.sleep(1)
            return ({'result': 'clean'}, 200)
        
        handler.meta_defender_api.check_result = slow_check_result
        
        result = await handler.handle_get(self.mock_request, self.mock_response)
        
        self.assertIn('result', result)
        self.assertEqual(result['result'], 'completed')
        self.assertEqual(result['outcome'], 'error')
        self.assertIn('Timeout', result['modifications'][0])
        self.assertEqual(self.mock_response.status_code, 200)
        logging.error.assert_called()

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    @patch('metadefender_menlo.api.handlers.result_handler.FileAnalyis')
    async def test_handle_get_with_allowlist_enabled(self, mock_file_analysis, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        test_config_with_allowlist = {
            'timeout': {
                'result': {
                    'enabled': False,
                    'value': 30
                }
            },
            'allowlist': {
                'enabled': True,
                'aws_profile': 'default',
                'db_table_name': 'test-table'
            }
        }
        
        handler = ResultHandler(config=test_config_with_allowlist)
        handler.meta_defender_api = Mock()
        handler.meta_defender_api.service_name = SERVICE.MetaDefenderCore
        handler.allowlist_handler.is_allowlist_enabled = Mock(return_value=True)
        handler.allowlist_handler.is_in_allowlist = Mock(return_value=(None, None))
        
        test_uuid = 'test-uuid-789'
        test_response = {'result': 'completed', 'outcome': 'clean'}
        
        self._setup_mock_request(test_uuid)
        
        handler.meta_defender_api.check_result = AsyncMock(
            return_value=(test_response, 200)
        )
        
        mock_file_analysis_instance = mock_file_analysis.return_value
        mock_file_analysis_instance.handle_response = AsyncMock(
            return_value=(test_response, 200)
        )
        
        result = await handler.handle_get(self.mock_request, self.mock_response)
        
        self.assertEqual(result, test_response)
        handler.allowlist_handler.is_in_allowlist.assert_called_once_with(test_uuid)


if __name__ == '__main__':
    unittest.main()
