import unittest
from unittest.mock import Mock, patch
import logging

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.file_metadata import InboundMetadataHandler

class TestInboundMetadataHandler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.application = Mock()
        self.application.ui_methods = {}  
        self.application.ui_modules = {} 
        self.request = Mock()
        
        self.handler = InboundMetadataHandler(
            application=self.application,
            request=self.request
        )
        
        self.original_logging_warning = logging.warning
        
        logging.warning = Mock()

    def tearDown(self):
        """Clean up after each test method."""
        logging.warning = self.original_logging_warning

    def test_post(self):
        """Test POST method."""
        self.handler.json_response = Mock()
        expected_message = "POST /api/v1/submit > Not implemented"
        expected_response = {"error": "Not implemented"}
        expected_status = 400

        self.handler.post()

        logging.warning.assert_called_once_with(expected_message)

        self.handler.json_response.assert_called_once_with(
            expected_response,
            expected_status
        )

    @patch('logging.warning')
    def test_post_with_logging_error(self, mock_logging):
        """Test POST method when logging raises an exception."""
        self.handler.json_response = Mock()
        mock_logging.return_value = None  
        self.handler.post()

        self.handler.json_response.assert_called_once_with(
            {"error": "Not implemented"},
            400
        )

        mock_logging.assert_called_once()

    def test_post_response_format(self):
        """Test the exact format and content of the POST response."""
        response_data = None
        response_status = None
        
        def capture_response(data, status):
            nonlocal response_data, response_status
            response_data = data
            response_status = status
            
        self.handler.json_response = capture_response

        self.handler.post()

        self.assertIsInstance(response_data, dict)
        self.assertIn('error', response_data)
        
        self.assertEqual(response_status, 400)


if __name__ == '__main__':
    unittest.main()
