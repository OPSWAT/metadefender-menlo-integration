import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from tornado.web import HTTPError

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.file_submit import FileSubmitHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class MockApplication:
    def __init__(self):
        self.ui_methods = {}
        self.ui_modules = {}

class TestFileSubmitHandler(unittest.TestCase):
    def setUp(self):
        self.mock_app = MockApplication()
        self.handler = FileSubmitHandler(application=self.mock_app, request=MagicMock())
        self.handler.metaDefenderAPI = MagicMock()
        self.handler.client_ip = '127.0.0.1'

    @patch('metadefender_menlo.api.file_submit_handler.logging.info')
    @patch('metadefender_menlo.api.file_submit_handler.logging.debug')
    @patch('metadefender_menlo.api.file_submit_handler.FileSubmit')
    @patch('metadefender_menlo.api.file_submit_handler.FileSubmitHandler.validateFile')
    async def test_post_successful(self, mock_validate, mock_filesubmit, mock_debug, mock_info):
        self.handler.request.headers = {'Authorization': 'test_apikey'}
        self.handler.request.files = {
            'file': [{'filename': 'test.txt', 'content_type': 'text/plain', 'body': b'file_content'}]
        }
        mock_validate.return_value = self.handler.request.files
        self.handler.metaDefenderAPI.submit_file = AsyncMock(return_value=({"response": "ok"}, 200))
        mock_filesubmit.return_value.handle_response.return_value = ({"response": "ok"}, 200)
        self.handler.json_response = MagicMock()

        await self.handler.post()

        mock_validate.assert_called_once()
        self.handler.metaDefenderAPI.submit_file.assert_called_once_with(
            'test.txt', b'file_content', metadata={}, apikey='test_apikey', ip='127.0.0.1'
        )
        self.handler.json_response.assert_called_once_with({"response": "ok"}, 200)
        mock_info.assert_called_once()
        mock_debug.assert_called()

    @patch('metadefender_menlo.api.file_submit_handler.logging.error')
    @patch('metadefender_menlo.api.file_submit_handler.FileSubmitHandler.validateFile')
    async def test_post_exception(self, mock_validate, mock_error):
        self.handler.request.headers = {'Authorization': 'test_apikey'}
        self.handler.request.files = {
            'file': [{'filename': 'test.txt', 'content_type': 'text/plain', 'body': b'file_content'}]
        }
        mock_validate.return_value = self.handler.request.files
        self.handler.metaDefenderAPI.submit_file = AsyncMock(side_effect=Exception("Submission error"))
        self.handler.json_response = MagicMock()

        await self.handler.post()

        self.handler.json_response.assert_called_once_with({}, 500)
        mock_error.assert_called()

    def test_validate_file_no_file(self):
        self.handler.request.files = {}

        with self.assertRaises(HTTPError) as context:
            self.handler.validateFile('test_apikey')

        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(str(context.exception), 'HTTP 400: Bad Request (No file uploaded)')

    def test_validate_file_too_many_files(self):
        self.handler.request.files = {
            'file1': [{'filename': 'file1.txt', 'content_type': 'text/plain', 'body': b'file1_content'}],
            'file2': [{'filename': 'file2.txt', 'content_type': 'text/plain', 'body': b'file2_content'}]
        }

        with self.assertRaises(HTTPError) as context:
            self.handler.validateFile('test_apikey')
        self.assertEqual(context.exception.status_code, 400)
        self.assertEqual(str(context.exception), 'HTTP 400: Bad Request (Too many files uploaded)')

    def test_validate_file_valid(self):
        self.handler.request.files = {
            'file': [{'filename': 'test.txt', 'content_type': 'text/plain', 'body': b'file_content'}]
        }

        files = self.handler.validateFile('test_apikey')
        self.assertEqual(files, self.handler.request.files)

    @patch('metadefender_menlo.api.file_submit_handler.logging.debug')
    async def test_post_logging_and_metadata(self, mock_debug):
        self.handler.request.headers = {'Authorization': 'test_apikey'}
        self.handler.request.files = {
            'file': [{'filename': 'test.txt', 'content_type': 'text/plain', 'body': b'file_content'}]
        }
        self.handler.request.arguments = {'arg1': 'value1', 'arg2': 'value2'}
        
        self.handler.validateFile = MagicMock(return_value=self.handler.request.files)
        self.handler.json_response = MagicMock()
        self.handler.metaDefenderAPI.submit_file = AsyncMock(return_value=({"response": "ok"}, 200))
        await self.handler.post()

        mock_debug.assert_any_call("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
            "headers": "arg1 : value1"
        }))
        mock_debug.assert_any_call("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
            "headers": "arg2 : value2"
        }))
        
    @patch('metadefender_menlo.api.file_submit_handler.logging.info')
    async def test_post_logging_info_called(self, mock_info):
        self.handler.request.headers = {'Authorization': 'test_apikey'}
        self.handler.request.files = {
            'file': [{'filename': 'test.txt', 'content_type': 'text/plain', 'body': b'file_content'}]
        }
        
        self.handler.validateFile = MagicMock(return_value=self.handler.request.files)
        self.handler.metaDefenderAPI.submit_file = AsyncMock(return_value=({"response": "ok"}, 200))
        self.handler.json_response = MagicMock()
        
        await self.handler.post()

        mock_info.assert_called_once()
        log_args = mock_info.call_args[0][0]
        self.assertIn('method', log_args)
        self.assertIn('fileName', log_args)
        self.assertIn('content_type', log_args)
        self.assertIn('dimension', log_args)

if __name__ == '__main__':
    unittest.main()
