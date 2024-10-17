import json
import unittest
from unittest.mock import MagicMock, patch, Mock, AsyncMock, _patch
import urllib.parse
import logging

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

class TestMetaDefenderCloudAPI(unittest.TestCase):

    def setUp(self):
        # Setup any required variables and the instance of the class
        self.settings = {'scanRule': 'test_rule'}
        self.url = 'https://testurl.com'
        self.apikey = 'test_apikey'
        self.api = MetaDefenderCloudAPI(self.settings, self.url, self.apikey)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_success(self, mock_async_client):
        # Mocking the response for the download function
        mock_response = AsyncMock()
        mock_response.content = b'Test file content'
        mock_response.status_code = 200
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result, status = await self.api._download_sanitized_file('https://example.com/file', self.apikey)

        self.assertEqual(result, b'Test file content')
        self.assertEqual(status, 200)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_error(self, mock_async_client):
        # Simulating an exception during the download
        mock_async_client.return_value.__aenter__.side_effect = Exception("Network Error")

        result, status = await self.api._download_sanitized_file('https://example.com/file', self.apikey)

        self.assertEqual(result['error'], "Network Error")
        self.assertEqual(status, 500)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file_success(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.content = b'{"sanitized": {"failure_reasons": []}}'
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result, status = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, "")
        self.assertEqual(status, 204)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file_error(self, mock_async_client):
        mock_async_client.return_value.__aenter__.side_effect = Exception("Network Error")
        
        result, status = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result['error'], "Network Error")
        self.assertEqual(status, 500)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    def test_parse_sanitized_data(self, mock_async_client):
        response = MagicMock()
        response.content = b'{"sanitized": {"key": "value"}}'
        result = self.api._parse_sanitized_data(response)

        self.assertEqual(result, {"key": "value"})

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_response(self, mock_logging):
        response = {"status": "ok"}
        http_status = 200

        self.api._log_response(response, http_status)

        mock_logging.info.assert_called_once_with(
            "{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "response": f"{response}", "status": f"{http_status}"
            })
        )

    def test_get_failure_reasons(self):
        sanitized_data = {"failure_reasons": ["reason1", "reason2"]}
        result = self.api._get_failure_reasons(sanitized_data)

        self.assertEqual(result, ["reason1", "reason2"])

    def test_get_failure_reasons_empty(self):
        sanitized_data = {}
        result = self.api._get_failure_reasons(sanitized_data)

        self.assertEqual(result, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        error = Exception("Test error")
        result, status = self.api._handle_error(error, self.apikey)

        self.assertEqual(result, {"error": "Test error"})
        self.assertEqual(status, 500)
        mock_logging.error.assert_called_once()

    def test_check_analysis_complete(self):
        json_response = {"sanitized": {"progress_percentage": 100}}
        result = self.api.check_analysis_complete(json_response)

        self.assertTrue(result)

    def test_check_analysis_complete_incomplete(self):
        json_response = {"sanitized": {"progress_percentage": 50}}
        result = self.api.check_analysis_complete(json_response)

        self.assertFalse(result)

    def test_check_analysis_complete_unexpected(self):
        json_response = {"unexpected_key": "value"}
        result = self.api.check_analysis_complete(json_response)

        self.assertFalse(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_get_submit_file_headers(self, mock_logging):
        filename = "test_file.txt"
        metadata = {}
        headers = self.api._get_submit_file_headers(filename, metadata)

        self.assertIn("filename", headers)
        self.assertIn("Content-Type", headers)
        self.assertEqual(headers["filename"], urllib.parse.quote(filename))
        self.assertEqual(headers["Content-Type"], "application/octet-stream")

    def test_check_analysis_complete_no_keys(self):
        json_response = {}
        result = self.api.check_analysis_complete(json_response)

        self.assertFalse(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_retrieve_sanitized_file_unauthorized(self, mock_async_client):
        mock_response = {"message": "Unauthorized"}
        mock_async_client.return_value.__aenter__.return_value.get.return_value = AsyncMock(status_code=401, json=AsyncMock(return_value=mock_response))

        result = await self.api.retrieve_sanitized_file("data_id", self.apikey, "1.1.1.1")

        self.assertEqual(result, (mock_response, 401))

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_exception(self, mock_async_client):
        mock_async_client.return_value.__aenter__.side_effect = Exception("Download Error")

        result, status = await self.api._download_sanitized_file("https://example.com/file", self.apikey)

        self.assertEqual(result['error'], "Download Error")
        self.assertEqual(status, 500)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_log_sanitization_result_with_failure_reasons(self, mock_logging):
        failure_reasons = ["Reason 1", "Reason 2"]
        result, status = self.api._log_sanitization_result(failure_reasons)

        self.assertEqual(status, 204)
        mock_logging.info.assert_called_with("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "message": "Sanitization failed with failure reasons.",
            "failure_reasons": failure_reasons,
            "status": status
        }))

    async def test_log_sanitization_result_no_reasons(self):
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging') as mock_logging:
            result, status = self.api._log_sanitization_result([])

            self.assertEqual(status, 204)
            mock_logging.info.assert_called_with("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Sanitized file not available!", "status": status
            }))

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error_logging(self, mock_logging):
        error = Exception("Test error")
        result = self.api._handle_error(error, self.apikey)
        self.assertEqual(result, ({"error": "Test error"}, 500))  
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file(self, mock_async_client):
        data_id = "12345"
        apikey = "your_api_key"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"sanitized": {"failure_reasons": ["some reason"]}}).encode('utf-8')
        
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file(data_id, apikey)

        self.assertEqual(result, ("", 204))
        mock_async_client.return_value.__aenter__.return_value.get.assert_called_once()

    def test_parse_sanitized_data(self):
        response = MagicMock()
        response.content = json.dumps({"sanitized": {"some_key": "some_value"}}).encode('utf-8')
        sanitized_data = self.api._parse_sanitized_data(response)
        self.assertEqual(sanitized_data, {"some_key": "some_value"})

    def test_handle_unauthorized(self):
        response = {"error": "Unauthorized"}
        http_status = 401
        result = self.api._handle_unauthorized(response, http_status)
        self.assertEqual(result, (response, http_status))

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        error_message = "Test error"
        
        # Act
        result = self.api._handle_error(Exception(error_message), "apikey")

        # Assert
        expected_result = {"error": error_message}
        expected_status = 500
        self.assertEqual(result[0], expected_result)  # Check the first part of the tuple
        self.assertEqual(result[1], expected_status)  # Check the second part of the tuple

        # Verify logging happened
        mock_logging.error.assert_called_once()

    @patch('httpx.AsyncClient.get')
    async def test_handle_no_sanitized_file(self, mock_get):
        # Mock the response
        mock_response = MagicMock()
        mock_response.content = json.dumps({"sanitized": {"failure_reasons": ["reason1", "reason2"]}}).encode()
        mock_get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file("data_id", "apikey")
        self.assertEqual(result, "", 204)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    @patch('httpx.AsyncClient.get')
    async def test_handle_error_logging(self, mock_get, mock_logging):
        mock_get.side_effect = Exception("Test error")
        
        result = await self.api._handle_no_sanitized_file("data_id", "apikey")

        # Assert logging was called
        mock_logging.error.assert_called_with(
            "{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Internal, repr(Exception("Test error"))),
            {'apikey': "apikey"}
        )
        self.assertEqual(result, {"error": "Test error"}, 500)

if __name__ == '__main__':
    unittest.main()