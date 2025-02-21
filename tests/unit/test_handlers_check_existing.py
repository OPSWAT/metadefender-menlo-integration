import logging
import unittest
from unittest.mock import Mock, patch, AsyncMock

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.handlers.check_existing import CheckExistingHandler

class TestCheckExistingHandler(unittest.TestCase):
    def setUp(self):
        # Create a mock application
        self.application = Mock()
        self.application.ui_methods = {}
        self.application.ui_modules = {}

        # Create a mock request
        self.request = Mock()
        self.request.connection = Mock()
        self.request.connection.context = {}

        # Create handler instance
        self.handler = CheckExistingHandler(
            application=self.application,
            request=self.request
        )

        # Mock handler attributes
        self.handler.metaDefenderAPI = Mock()
        self.handler.client_ip = '127.0.0.1'
        self.handler.json_response = Mock()

        # Store original logging functions
        self.original_logging_info = logging.info
        self.original_logging_error = logging.error

        # Mock logging functions
        logging.info = Mock()
        logging.error = Mock()

    def tearDown(self):
        logging.info = self.original_logging_info
        logging.error = self.original_logging_error

    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_success_path(self, mock_check_existing):
        test_sha256 = 'a' * 64
        test_apikey = 'test_apikey'
        initial_response = {
        'scan_results': {'scan_all_result_i': 0},
        'file_info': {'file_size': 1024}
        }
        expected_response = {
            **initial_response,
            'sha256': test_sha256
        }

        self.handler.get_query_argument = Mock(return_value=test_sha256)

        self.handler.request.headers = {'Authorization': test_apikey}

        self.handler.metaDefenderAPI.hash_lookup = AsyncMock(
            return_value=(initial_response, 200)
        )

        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response.return_value = (expected_response, 200)

        await self.handler.get()

        self.handler.get_query_argument.assert_called_once_with('sha256')

        self.assertEqual(self.handler.request.headers.get('Authorization'), test_apikey)

        logging.info.assert_called_once_with(
            "{0} > {1} > {2}".format(
                "MenloPlugin",
                "Request",
                {
                    "method": "GET",
                    "endpoint": f"/api/v1/result/{test_sha256}"
                }
            )
        )

        self.handler.metaDefenderAPI.hash_lookup.assert_called_once_with(
            test_sha256, test_apikey, self.handler.client_ip
        )

        json_response, _ = mock_check_existing_instance.handle_response.return_value
        self.assertIn('sha256', json_response)  

        mock_check_existing_instance.handle_response.assert_called_once_with(
            200, initial_response
        )
        self.handler.json_response.assert_called_once_with(expected_response, 200)


    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_error_path(self, mock_check_existing):
        test_sha256 = 'a' * 64
        test_apikey = 'test_apikey'
        test_error = Exception("Test error")

        self.handler.get_query_argument = Mock(return_value=test_sha256)
        self.handler.request.headers = {'Authorization': test_apikey}

        self.handler.metaDefenderAPI.hash_lookup = AsyncMock(
            side_effect=test_error
        )

        await self.handler.get()

        logging.error.assert_called_once_with(
            "{0} > {1} > {2}".format(
                SERVICE.MetaDefenderAPI,
                TYPE.Response,
                {"error": repr(test_error)}
            ),
            {'apikey': test_apikey}
        )

        self.handler.json_response.assert_called_once_with({}, 500)

    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_invalid_input(self):
        """Test handling of invalid input parameters."""
        self.handler.get_query_argument = Mock(side_effect=Exception("Missing argument"))
        self.handler.request.headers = {'Authorization': 'test_apikey'}

        await self.handler.get()

        self.handler.json_response.assert_called_once_with({}, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_checkexisting_error(self, mock_check_existing):
        """Test handling of CheckExisting errors."""
        test_sha256 = 'a' * 64
        test_apikey = 'test_apikey'
        initial_response = {'key': 'value'}

        self.handler.get_query_argument = Mock(return_value=test_sha256)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.hash_lookup = AsyncMock(
            return_value=(initial_response, 200)
        )

        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response.side_effect = Exception("CheckExisting error")

        await self.handler.get()

        self.handler.json_response.assert_called_once_with({}, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_handle_response_error(self, mock_check_existing):
        """Test the error when CheckExisting handles response incorrectly."""
        test_sha256 = 'a' * 64
        test_apikey = 'test_apikey'
        initial_response = {'key': 'value'}

        self.handler.get_query_argument = Mock(return_value=test_sha256)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.hash_lookup = AsyncMock(
            return_value=(initial_response, 200)
        )

        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response.side_effect = Exception("Handle response error")

        await self.handler.get()

        logging.error.assert_called_once()  
        self.handler.json_response.assert_called_once_with({}, 500)
    
    @patch('metadefender_menlo.api.responses.check_existing.CheckExisting')
    async def test_get_handle_response_error(self, mock_check_existing):
        test_sha256 = 'a' * 64
        test_apikey = 'test_apikey'
        initial_response = {'key': 'value'}

        self.handler.get_query_argument = Mock(return_value=test_sha256)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.hash_lookup = AsyncMock(
        return_value=(initial_response, 200)
    )

        mock_check_existing_instance = mock_check_existing.return_value
        mock_check_existing_instance.handle_response.side_effect = Exception("Handle response error")

        await self.handler.get()

        logging.error.assert_called_once()  
        self.handler.json_response.assert_called_once_with({}, 500)

if __name__ == '__main__':
    unittest.main()