import unittest
from unittest.mock import Mock, patch, AsyncMock
import logging

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.retrieve_sanitized import RetrieveSanitizedHandler

class TestRetrieveSanitizedHandler(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test case."""
        mock_application = Mock()
        mock_application.ui_methods = {'method_name': Mock()}

        self.handler = RetrieveSanitizedHandler(
            application=mock_application,
            request=Mock(),
        )
        
        self.handler.metaDefenderAPI = Mock()
        self.handler.client_ip = '127.0.0.1'
        
        self.original_logging_info = logging.info
        self.original_logging_error = logging.error
        
        logging.info = Mock()
        logging.error = Mock()

    def tearDown(self):
        """Clean up after each test case."""
        logging.info = self.original_logging_info
        logging.error = self.original_logging_error

    def test_init(self):
        """Test handler initialization."""
        self.assertIsInstance(self.handler, RetrieveSanitizedHandler)

    @patch('metadefender_menlo.api.responses.retrieve_sanitized.RetrieveSanitized')
    async def test_get_success(self, mock_retrieve_sanitized):
        """Test successful GET request."""
        test_uuid = 'test-uuid-123'
        test_apikey = 'test-apikey-456' # gitleaks:allow
        test_file = b'test file content'
        test_status_code = 200
        
        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.retrieve_sanitized_file = AsyncMock(
            return_value=(test_file, test_status_code)
        )
        
        mock_sanitized_instance = mock_retrieve_sanitized.return_value
        mock_sanitized_instance.handle_response.return_value = (test_file, test_status_code)
        
        self.handler.stream_response = Mock()

        await self.handler.get()

        self.handler.get_argument.assert_called_once_with('uuid')
        self.handler.metaDefenderAPI.retrieve_sanitized_file.assert_called_once_with(
            uuid=test_uuid,
            apikey=test_apikey,
            client_ip=self.handler.client_ip
        )
        mock_sanitized_instance.handle_response.assert_called_once_with(
            status_code=test_status_code,
            file=test_file
        )
        self.handler.stream_response.assert_called_once_with(test_file, test_status_code)
        logging.info.assert_called_once()

    async def test_get_missing_uuid(self):
        """Test GET request with missing UUID."""
        self.handler.get_argument = Mock(return_value=None)
        self.handler.json_response = Mock()

        await self.handler.get()

        self.handler.json_response.assert_called_once_with(
            {'error': 'Missing required parameter: uuid'},
            400
        )

    async def test_get_missing_apikey(self):
        """Test GET request with missing API key."""
        self.handler.get_argument = Mock(return_value='test-uuid')
        self.handler.request.headers = {}
        self.handler.json_response = Mock()

        await self.handler.get()

        self.handler.json_response.assert_called_once_with(
            {'error': 'Missing required header: Authorization'},
            401
        )

    @patch('metadefender_menlo.api.responses.retrieve_sanitized.RetrieveSanitized')
    async def test_get_sanitize_error(self, mock_retrieve_sanitized):
        """Test GET request with sanitization error."""
        test_uuid = 'test-uuid-123'
        test_apikey = 'test-apikey-456' # gitleaks:allow
        test_file = b'test file content'
        test_status_code = 200
        
        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.retrieve_sanitized_file = AsyncMock(
            return_value=(test_file, test_status_code)
        )
        
        mock_sanitized_instance = mock_retrieve_sanitized.return_value
        mock_sanitized_instance.handle_response.side_effect = Exception('Sanitization failed')
        
        self.handler.json_response = Mock()

        await self.handler.get()

        self.handler.json_response.assert_called_once_with(
            {'error': 'Error processing sanitized file'},
            500
        )
        logging.error.assert_called_once()

    async def test_get_general_error(self):
        """Test GET request with general error."""
        self.handler.get_argument = Mock(side_effect=Exception('General error'))
        self.handler.json_response = Mock()

        await self.handler.get()

        self.handler.json_response.assert_called_once_with(
            {'error': 'Internal server error'},
            500
        )
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.responses.retrieve_sanitized.RetrieveSanitized')
    async def test_get_api_error(self, mock_retrieve_sanitized):
        """Test GET request with API error."""
        test_uuid = 'test-uuid-123'
        test_apikey = 'test-apikey-456' # gitleaks:allow
        
        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.retrieve_sanitized_file = AsyncMock(
            side_effect=Exception('API error')
        )
        
        self.handler.json_response = Mock()

        await self.handler.get()

        self.handler.json_response.assert_called_once_with(
            {'error': 'Internal server error'},
            500
        )
        logging.error.assert_called_once()


if __name__ == '__main__':
    unittest.main()
