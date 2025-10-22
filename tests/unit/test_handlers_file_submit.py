import unittest
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import logging
import os
import sys
import asyncio
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.submit_handler import SubmitHandler, stream_file, AsyncFileStream, submit_handler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from fastapi import Request, Response
from starlette.datastructures import FormData, UploadFile
import io


class TestSubmitHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'timeout': {
                'submit': {
                    'enabled': False,
                    'value': 30
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        self.handler = SubmitHandler(config=self.test_config)
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

    def _setup_mock_request(self, content_type="multipart/form-data", has_file=True):
        self.mock_request.headers = MagicMock()
        self.mock_request.headers.get = Mock(return_value=content_type)
        self.mock_request.client = MagicMock()
        self.mock_request.client.host = '127.0.0.1'
        
        if has_file:
            mock_upload = MagicMock(spec=UploadFile)
            mock_upload.filename = 'test.txt'
            mock_upload.file = io.BytesIO(b'test content')
            mock_upload.close = AsyncMock()
            
            mock_form = MagicMock(spec=FormData)
            mock_form.get = Mock(side_effect=lambda key: {
                'files': mock_upload,
                'userid': 'test_user',
                'srcuri': 'https://example.com',
                'filename': 'test.txt'
            }.get(key))
            
            self.mock_request.form = AsyncMock(return_value=mock_form)
        else:
            mock_form = MagicMock(spec=FormData)
            mock_form.get = Mock(return_value=None)
            self.mock_request.form = AsyncMock(return_value=mock_form)

    @patch('metadefender_menlo.api.handlers.submit_handler.SubmitResponse')
    async def test_handle_post_success(self, mock_submit_response):
        test_response = {'uuid': 'test-uuid-123', 'result': 'accepted'}
        test_status = 200

        self._setup_mock_request()
        self.handler.meta_defender_api.submit = AsyncMock(
            return_value=(test_response, test_status)
        )

        mock_submit_response_instance = mock_submit_response.return_value
        mock_submit_response_instance.handle_response = AsyncMock(
            return_value=(test_response, test_status)
        )

        result = await self.handler.handle_post(self.mock_request, self.mock_response)

        self.assertEqual(result, test_response)
        self.assertEqual(self.mock_response.status_code, test_status)
        logging.info.assert_called()
        self.handler.meta_defender_api.submit.assert_called_once()

    async def test_handle_post_invalid_content_type(self):
        self._setup_mock_request(content_type="application/json")
        result = await self.handler.handle_post(self.mock_request, self.mock_response)
        
        self.assertEqual(result, {'error': 'Content-Type must be multipart/form-data'})
        self.assertEqual(self.mock_response.status_code, 400)

    async def test_handle_post_no_file(self):
        self._setup_mock_request(has_file=False)
        result = await self.handler.handle_post(self.mock_request, self.mock_response)
        
        self.assertEqual(result, {'error': 'No file uploaded'})
        self.assertEqual(self.mock_response.status_code, 400)

    @patch('metadefender_menlo.api.handlers.submit_handler.SubmitResponse')
    async def test_handle_post_api_error(self, mock_submit_response):
        self._setup_mock_request()
        self.handler.meta_defender_api.submit = AsyncMock(
            side_effect=Exception("API Error")
        )

        result = await self.handler.handle_post(self.mock_request, self.mock_response)

        self.assertEqual(result, {})
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    @patch('metadefender_menlo.api.handlers.submit_handler.SubmitResponse')
    async def test_handle_post_with_timeout_enabled(self, mock_submit_response, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        test_config_with_timeout = {
            'timeout': {
                'submit': {
                    'enabled': True,
                    'value': 0.1
                }
            },
            'allowlist': {
                'enabled': False
            }
        }
        
        handler = SubmitHandler(config=test_config_with_timeout)
        handler.meta_defender_api = Mock()
        handler.meta_defender_api.service_name = SERVICE.meta_defender_core
        
        self._setup_mock_request()
        
        async def slow_submit(*args):
            import asyncio
            await asyncio.sleep(1)
            return ({'uuid': 'test-uuid'}, 200)
        
        handler.meta_defender_api.submit = slow_submit
        
        result = await handler.handle_post(self.mock_request, self.mock_response)
        
        self.assertEqual(result['result'], 'skip')
        self.assertEqual(result['uuid'], '')
        self.assertEqual(self.mock_response.status_code, 500)
        logging.error.assert_called()

    async def test_process_result(self):
        mock_upload = MagicMock(spec=UploadFile)
        mock_upload.file = io.BytesIO(b'test content')
        metadata = {'userid': 'test_user', 'filename': 'test.txt'}
        
        self.handler.meta_defender_api.submit = AsyncMock(
            return_value=({'uuid': 'test-uuid'}, 200)
        )
        
        result_json, result_status = await self.handler.process_result(mock_upload, metadata)
        
        self.handler.meta_defender_api.submit.assert_called_once_with(
            mock_upload.file, metadata, self.handler.apikey, self.handler.client_ip
        )
        self.assertEqual(result_status, 200)

    async def test_get_uuid_and_add_to_allowlist_disabled(self):
        json_response = {'uuid': 'test-uuid'}
        http_status = 200
        metadata = {'srcuri': 'example.com', 'filename': 'test.txt'}
        
        self.handler.allowlist_handler = Mock()
        self.handler.allowlist_handler.is_allowlist_enabled.return_value = False
        
        await self.handler.get_uuid_and_add_to_allowlist(json_response, http_status, metadata)
        
        self.handler.allowlist_handler.is_allowlist_enabled.assert_called_once()
        self.handler.allowlist_handler.add_to_allowlist.assert_not_called()

    async def test_get_uuid_and_add_to_allowlist_enabled(self):
        json_response = {'uuid': 'test-uuid'}
        http_status = 200
        metadata = {'srcuri': 'example.com', 'filename': 'test.txt'}
        
        self.handler.allowlist_handler = Mock()
        self.handler.allowlist_handler.is_allowlist_enabled.return_value = True
        
        await self.handler.get_uuid_and_add_to_allowlist(json_response, http_status, metadata)
        
        self.handler.allowlist_handler.is_allowlist_enabled.assert_called_once()
        self.handler.allowlist_handler.add_to_allowlist.assert_called_once_with(
            200, 'test-uuid', 'example.com', 'test.txt', self.handler.apikey
        )

    async def test_stream_file_function(self):
        """Test the stream_file function"""
        file_obj = io.BytesIO(b'test content')
        chunks = []
        async for chunk in stream_file(file_obj):
            chunks.append(chunk)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], b'test content')

    async def test_async_file_stream_class(self):
        """Test the AsyncFileStream class"""
        file_obj = io.BytesIO(b'stream test')
        stream = AsyncFileStream(file_obj)
        
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0], b'stream test')

    @patch('metadefender_menlo.api.handlers.submit_handler.SubmitHandler')
    async def test_submit_handler_function(self, mock_submit_handler_class):
        """Test the submit_handler function"""
        mock_request = MagicMock(spec=Request)
        mock_response = MagicMock(spec=Response)
        mock_request.app.state.config = self.test_config
        
        mock_handler_instance = mock_submit_handler_class.return_value
        mock_handler_instance.handle_post = AsyncMock(return_value={'result': 'success'})
        
        result = await submit_handler(mock_request, mock_response)
        
        mock_submit_handler_class.assert_called_once_with(self.test_config)
        mock_handler_instance.handle_post.assert_called_once_with(mock_request, mock_response)
        self.assertEqual(result, {'result': 'success'})

    @patch('metadefender_menlo.api.handlers.submit_handler.SubmitResponse')
    async def test_handle_post_with_content_length_calculation(self, mock_submit_response):
        """Test content length calculation for MetaDefenderCore"""
        test_response = {'uuid': 'test-uuid', 'result': 'accepted'}
        test_status = 200

        self._setup_mock_request()
        self.handler.meta_defender_api.service_name = SERVICE.meta_defender_core
        
        # Mock the upload file with content
        mock_upload = MagicMock(spec=UploadFile)
        mock_upload.filename = 'test.txt'
        mock_file = io.BytesIO(b'test content for length calculation')
        mock_upload.file = mock_file
        mock_upload.close = AsyncMock()
        
        mock_form = MagicMock(spec=FormData)
        mock_form.get = Mock(side_effect=lambda key: {
            'files': mock_upload,
            'userid': 'test_user',
            'srcuri': 'https://example.com',
            'filename': 'test.txt'
        }.get(key))
        
        self.mock_request.form = AsyncMock(return_value=mock_form)
        
        self.handler.meta_defender_api.submit = AsyncMock(
            return_value=(test_response, test_status)
        )

        mock_submit_response_instance = mock_submit_response.return_value
        mock_submit_response_instance.handle_response = AsyncMock(
            return_value=(test_response, test_status)
        )

        result = await self.handler.handle_post(self.mock_request, self.mock_response)

        # Verify content-length was calculated
        self.handler.meta_defender_api.submit.assert_called_once()
        call_args = self.handler.meta_defender_api.submit.call_args[0]
        metadata = call_args[1]
        self.assertIn('content-length', metadata)
        self.assertEqual(metadata['content-length'], len(b'test content for length calculation'))

if __name__ == '__main__':
    unittest.main()