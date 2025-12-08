import unittest
from unittest.mock import MagicMock, Mock, patch, AsyncMock
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.base_handler import BaseHandler, request_id_context, request_context
from fastapi import Request, Response
from fastapi.responses import StreamingResponse


class TestBaseHandler(unittest.IsolatedAsyncioTestCase):

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        self.mock_api = MagicMock()
        mock_get_instance.return_value = self.mock_api
        
        self.config = {
            'allowlist': {
                'enabled': False
            }
        }
        self.handler = BaseHandler(self.config)
        
        self.mock_request = MagicMock(spec=Request)
        self.mock_request.headers = MagicMock()
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = '127.0.0.1'
        
        self.mock_response = MagicMock(spec=Response)

    def test_initialization(self):
        self.assertIsNotNone(self.handler.meta_defender_api)
        self.assertIsNone(self.handler.client_ip)
        self.assertIsNone(self.handler.apikey)
        self.assertIsNone(self.handler.handler_timeout)
        self.assertEqual(self.handler.config, self.config)

    def test_prepare_request_scenarios(self):
        self.mock_request.headers.get = MagicMock(side_effect=lambda key, default=None: {
            'request-id': 'test-request-id',
            'X-Real-IP': '192.0.2.1',
            'Authorization': 'test-api-key'
        }.get(key, default))
        
        self.handler.prepare_request(self.mock_request)
        
        self.assertEqual(request_id_context.get(), 'test-request-id')
        self.assertEqual(request_context.get(), self.mock_request)
        self.assertEqual(self.handler.client_ip, '192.0.2.1')
        self.assertEqual(self.handler.apikey, 'test-api-key')

        self.mock_request.headers.get = MagicMock(side_effect=lambda key, default=None: {
            'Authorization': 'test-api-key'
        }.get(key, default))
        
        self.handler.prepare_request(self.mock_request)
        
        request_id = request_id_context.get()
        self.assertIsNotNone(request_id)
        self.assertNotEqual(request_id, '')
        self.assertEqual(request_context.get(), self.mock_request)

        self.mock_request.headers.get = MagicMock(side_effect=lambda key, default=None: {
            'X-Forwarded-For': '198.51.100.1',
            'Authorization': 'test-api-key'
        }.get(key, default))
        
        self.handler.prepare_request(self.mock_request)
        self.assertEqual(self.handler.client_ip, '198.51.100.1')

        self.mock_request.headers.get = Mock(return_value=None)
        self.mock_request.client.host = '127.0.0.1'
        
        self.handler.prepare_request(self.mock_request)
        self.assertEqual(self.handler.client_ip, '127.0.0.1')

    @patch('logging.info')
    def test_json_response_scenarios(self, mock_logging):
        json_data = {'key': 'value', 'status': 'success'}
        status_code = 200
        
        result = self.handler.json_response(self.mock_response, json_data, status_code)
        
        self.assertEqual(result, json_data)
        self.assertEqual(self.mock_response.status_code, status_code)
        mock_logging.assert_called()

        json_data = {'key': 'value'}
        status_code = 204
        
        result = self.handler.json_response(self.mock_response, json_data, status_code)
        
        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, status_code)
        mock_logging.assert_called()

        json_data = {'error': 'Something went wrong'}
        status_code = 500
        
        result = self.handler.json_response(self.mock_response, json_data, status_code)
        
        self.assertEqual(result, json_data)
        self.assertEqual(self.mock_response.status_code, status_code)
        mock_logging.assert_called()

    @patch('logging.info')
    def test_stream_response(self, mock_logging):
        mock_resp = MagicMock()
        mock_resp.aiter_raw = MagicMock(return_value=iter([b'chunk1', b'chunk2']))
        mock_resp.headers = MagicMock()
        mock_resp.headers.get = MagicMock(side_effect=lambda key, default=None: {
            'Content-Type': 'application/pdf',
            'Content-Disposition': 'attachment; filename="test.pdf"'
        }.get(key, default))
        mock_resp.aclose = AsyncMock()
        
        mock_client = MagicMock()
        
        result = self.handler.stream_response(mock_resp, mock_client, 200)
        
        self.assertIsInstance(result, StreamingResponse)
        mock_logging.assert_called_once()

    async def test_process_result_with_timeout_scenarios(self):
        self.handler.handler_timeout = None
        
        async def mock_process_result(arg1, arg2):
            await asyncio.sleep(0)
            return arg1 + arg2
        
        self.handler.process_result = mock_process_result
        
        result = await self.handler.process_result_with_timeout(5, 10)
        self.assertEqual(result, 15)

        self.handler.handler_timeout = 5
        
        async def mock_process_result(value):
            await asyncio.sleep(0.01)
            return value * 2
        
        self.handler.process_result = mock_process_result
        
        result = await self.handler.process_result_with_timeout(10)
        self.assertEqual(result, 20)

        self.handler.handler_timeout = 0.1
        
        async def mock_process_result():
            await asyncio.sleep(1)
            return "completed"
        
        self.handler.process_result = mock_process_result
        
        with self.assertRaises(asyncio.TimeoutError):
            await self.handler.process_result_with_timeout()

    async def test_process_result_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await self.handler.process_result()


if __name__ == '__main__':
    unittest.main()
