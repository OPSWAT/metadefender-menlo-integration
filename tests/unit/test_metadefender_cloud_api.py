import json
import unittest
from unittest.mock import patch, Mock, AsyncMock
import urllib.parse

import sys
import os

import httpx
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

class TestMetaDefenderCloudAPI(unittest.TestCase):
    
    def setUp(self):
        self.settings = {'scanRule': 'test_rule'}
        self.url = 'https://test.url'
        self.apikey = 'test_apikey'
        self.api = MetaDefenderCloudAPI(self.settings, self.url, self.apikey)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._download_sanitized_file')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_no_sanitized_file')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_unauthorized')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._log_response')
    async def test_retrieve_sanitized_file_complete(
        self, mock_log_response, mock_handle_unauthorized, mock_handle_no_file, mock_download_file, mock_request
    ):
        """Test retrieving sanitized file for multiple paths: successful, unauthorized, no file."""
        # Test case for successful retrieval and download
        mock_request.return_value = ({"sanitizedFilePath": "https://test.file"}, 200)
        mock_download_file.return_value = (b"file_content", 200)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')
        self.assertEqual(status, 200)
        self.assertEqual(response, b"file_content")
        mock_log_response.assert_called_once()

        # Test case for unauthorized access
        mock_request.return_value = ({"error": "Unauthorized"}, 401)
        mock_handle_unauthorized.return_value = ({"error": "Unauthorized"}, 401)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')
        self.assertEqual(status, 401)
        self.assertEqual(response, {"error": "Unauthorized"})
        mock_handle_unauthorized.assert_called_once()

        # Test case for no sanitized file available
        mock_request.return_value = ({"sanitizedFilePath": ""}, 200)
        mock_handle_no_file.return_value = ("", 204)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')
        self.assertEqual(status, 204)
        self.assertEqual(response, "")
        mock_handle_no_file.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    def test_log_response(self, mock_logging_info):
        """Test that logging happens correctly for responses."""
        response_data = {"response": "test_response"}
        http_status = 200

        # Call the method
        self.api._log_response(response_data, http_status)

        # Assert that logging was called
        mock_logging_info.assert_called_once()

        # Retrieve the actual arguments passed to the logging call
        log_args = mock_logging_info.call_args[0][0]

        # Now check the structure of the log message without worrying about the exact string format
        self.assertIn(SERVICE.MetaDefenderCloud, log_args)
        self.assertIn(TYPE.Response, log_args)
        self.assertIn("response", log_args)
        self.assertIn("status", log_args)
        self.assertIn("test_response", log_args)
        self.assertIn("200", log_args)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    def test_handle_unauthorized(self, mock_logging_info):
        """Test handling unauthorized responses."""
        response, status = self.api._handle_unauthorized({"error": "Unauthorized"}, 401)
        self.assertEqual(status, 401)
        self.assertEqual(response, {"error": "Unauthorized"})
        mock_logging_info.assert_called_once_with(
            "{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Unauthorized request", "status": 401
            })
        )

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_error')
    async def test_download_sanitized_file_success(self, mock_handle_error, mock_client):
        """Test downloading sanitized file successfully."""
        mock_response = Mock()
        mock_response.content = b"file_content"
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        response, status = await self.api._download_sanitized_file('https://test.file', 'test_apikey')
        self.assertEqual(status, 200)
        self.assertEqual(response, b"file_content")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_error')
    async def test_download_sanitized_file_failure(self, mock_handle_error, mock_client):
        """Test handling error when downloading sanitized file fails."""
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download error")
        mock_handle_error.return_value = ({"error": "Download error"}, 500)

        response, status = await self.api._download_sanitized_file('https://test.file', 'test_apikey')
        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "Download error"})
        mock_handle_error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file(self, mock_client):
        """Test handling scenario when no sanitized file is available."""
        mock_response = Mock()
        mock_response.content = json.dumps({"sanitized": {}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        response, status = await self.api._handle_no_sanitized_file('test_id', 'test_apikey')
        self.assertEqual(status, 204)
        self.assertEqual(response, "")

    def test_parse_sanitized_data(self):
        """Test parsing sanitized data from a response."""
        mock_response = Mock()
        mock_response.content = json.dumps({"sanitized": {"key": "value"}}).encode('utf-8')
        sanitized_data = self.api._parse_sanitized_data(mock_response)
        self.assertEqual(sanitized_data, {"key": "value"})

    def test_get_failure_reasons(self):
        """Test extracting failure reasons from sanitized data."""
        sanitized_data = {"failure_reasons": "Some reason"}
        failure_reasons = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(failure_reasons, "Some reason")

        sanitized_data = {"reason": "Another reason"}
        failure_reasons = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(failure_reasons, "Another reason")

        sanitized_data = {}
        failure_reasons = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(failure_reasons, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    def test_log_sanitization_result(self, mock_logging_info):
        """Test logging sanitization results."""
        failure_reasons = "Some failure reason"
        response, status = self.api._log_sanitization_result(failure_reasons)
        self.assertEqual(status, 204)
        self.assertEqual(response, "")
        mock_logging_info.assert_called_once_with(
            "{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Sanitization failed with failure reasons.",
                "failure_reasons": failure_reasons,
                "status": status
            })
        )

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.error')
    def test_handle_error(self, mock_logging_error):
        """Test error handling and logging."""
        error = Exception("An error occurred")
        response, status = self.api._handle_error(error, 'test_apikey')
        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "An error occurred"})
        mock_logging_error.assert_called_once_with(
            "{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Internal, repr(error)),
            {'apikey': 'test_apikey'}
        )

    def test_get_submit_file_headers(self):
        """Test _get_submit_file_headers method."""
        filename = "testfile.txt"
        metadata = {}  # You could add relevant metadata if needed
        headers = self.api._get_submit_file_headers(filename, metadata)

        expected_headers = {
            "filename": urllib.parse.quote(filename),
            "Content-Type": "application/octet-stream",
            "rule": self.settings['scanRule']
        }
        self.assertEqual(headers, expected_headers)

    def test_check_analysis_complete(self):
        """Test check_analysis_complete method."""
        # Test when progress is 100 (complete)
        json_response = {"sanitized": {"progress_percentage": 100}}
        result = self.api.check_analysis_complete(json_response)
        self.assertTrue(result)

        # Test when progress is less than 100 (not complete)
        json_response = {"sanitized": {"progress_percentage": 50}}
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)

        # Test when sanitized key is missing
        json_response = {}
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)

        # Test when sanitized key exists but progress_percentage is missing
        json_response = {"sanitized": {}}
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)
    
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.error')
    def test_handle_connection_error(self, mock_logging_error):
        """Test handling connection error."""
        error = ConnectionError("A connection error occurred")
        response, status = self.api._handle_error(error, 'test_apikey')
        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "A connection error occurred"})
        mock_logging_error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file_no_failure_reasons(self, mock_client):
        """Test handling no sanitized file with no failure reasons."""
        mock_response = Mock()
        mock_response.content = json.dumps({"sanitized": {}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        response, status = await self.api._handle_no_sanitized_file('test_id', 'test_apikey')
        self.assertEqual(status, 204)
        self.assertEqual(response, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    def test_log_sanitization_result_no_failure_reasons(self, mock_logging_info):
        """Test logging sanitization results with no failure reasons."""
        failure_reasons = ""
        response, status = self.api._log_sanitization_result(failure_reasons)
        self.assertEqual(status, 204)
        self.assertEqual(response, "")
        mock_logging_info.assert_called_once_with(
            "{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Sanitized file not available!",
                "status": status
            })
        )

    def test_parse_sanitized_data_edge_cases(self):
        """Test parsing sanitized data for edge cases."""
        # Test with empty response
        mock_response = Mock()
        mock_response.content = json.dumps({}).encode('utf-8')
        sanitized_data = self.api._parse_sanitized_data(mock_response)
        self.assertEqual(sanitized_data, {})

        # Test with non-sanitized content
        mock_response = Mock()
        mock_response.content = json.dumps({"non_sanitized": {"key": "value"}}).encode('utf-8')
        sanitized_data = self.api._parse_sanitized_data(mock_response)
        self.assertEqual(sanitized_data, {})

    def test_get_failure_reasons_edge_cases(self):
        """Test edge cases for failure reasons."""
        # Test with empty sanitized data
        sanitized_data = {}
        failure_reasons = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(failure_reasons, "")

        # Test with missing keys
        sanitized_data = {"unrelated_key": "Some reason"}
        failure_reasons = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(failure_reasons, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_error')
    async def test_download_sanitized_file_timeout(self, mock_handle_error, mock_client):
        """Test handling timeout when downloading sanitized file."""
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout error")
        mock_handle_error.return_value = ({"error": "Timeout error"}, 500)

        response, status = await self.api._download_sanitized_file('https://test.file', 'test_apikey')
        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "Timeout error"})
        mock_handle_error.assert_called_once()

    def test_get_submit_file_headers_missing_headers(self):
        """Test missing or incorrect headers in _get_submit_file_headers."""
        filename = "testfile.txt"
        metadata = None
        headers = self.api._get_submit_file_headers(filename, metadata)

        self.assertIn("filename", headers)
        self.assertIn("Content-Type", headers)
        self.assertIn("rule", headers)
        self.assertEqual(headers["rule"], "test_rule")

if __name__ == '__main__':
    unittest.main()