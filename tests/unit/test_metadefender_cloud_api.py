import unittest
from unittest import mock, IsolatedAsyncioTestCase
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import httpx
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE


class TestMetaDefenderCloudAPI(IsolatedAsyncioTestCase):

    def setUp(self):
        self.settings = {'scanRule': 'default_rule'}
        self.api = MetaDefenderCloudAPI(settings=self.settings, url='http://example.com', apikey='test_api_key')

    def test_get_submit_file_headers(self):
        headers = self.api._get_submit_file_headers('testfile.txt', {})
        self.assertIn("filename", headers)
        self.assertIn("Content-Type", headers)
        self.assertIn("rule", headers)
        self.assertEqual(headers["filename"], "testfile.txt")
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertEqual(headers["rule"], "default_rule")
        
        # Check logging for headers
        with mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging') as mock_logging:
            self.api._get_submit_file_headers('testfile.txt', {})
            mock_logging.debug.assert_called_once()

    def test_check_analysis_complete(self):
        # Test with 100% completion
        json_response = {
            "sanitized": {
                "progress_percentage": 100
            }
        }
        self.assertTrue(self.api.check_analysis_complete(json_response))

        # Test with less than 100% completion
        json_response = {
            "sanitized": {
                "progress_percentage": 50
            }
        }
        self.assertFalse(self.api.check_analysis_complete(json_response))

        # Test with missing keys
        json_response = {}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_retrieve_sanitized_file_success(self, mock_async_client):
        mock_response = mock.AsyncMock()
        mock_response.json.return_value = {"sanitizedFilePath": "http://example.com/sanitized_file"}
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        with mock.patch.object(self.api, '_download_sanitized_file', return_value=(b'test content', 200)) as mock_download:
            result = await self.api.retrieve_sanitized_file('test_data_id', 'test_api_key', '192.168.1.1')
            self.assertEqual(result, (b'test content', 200))
            mock_download.assert_called_once()

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_retrieve_sanitized_file_no_file(self, mock_async_client):
        mock_response = mock.AsyncMock()
        mock_response.json.return_value = {"sanitizedFilePath": ""}
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        with mock.patch.object(self.api, '_handle_no_sanitized_file', return_value=("", 204)) as mock_handle:
            result = await self.api.retrieve_sanitized_file('test_data_id', 'test_api_key', '192.168.1.1')
            self.assertEqual(result, ("", 204))
            mock_handle.assert_called_once()

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_response(self, mock_logging):
        self.api._log_response({"key": "value"}, 200)
        mock_logging.info.assert_called_once()

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_unauthorized(self, mock_logging):
        _, status = self.api._handle_unauthorized({"message": "Unauthorized"}, 401)
        self.assertEqual(status, 401)
        mock_logging.info.assert_called_once_with(mock.ANY)

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_success(self, mock_async_client):
        mock_response = mock.AsyncMock()
        mock_response.content = b'Test sanitized file content'
        mock_response.status_code = 200
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        content, status = await self.api._download_sanitized_file('http://example.com/sanitized_file', 'test_api_key')
        self.assertEqual(content, b'Test sanitized file content')
        self.assertEqual(status, 200)

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_error(self, mock_async_client):
        mock_async_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download error")

        result = await self.api._download_sanitized_file('http://example.com/sanitized_file', 'test_api_key')
        self.assertIn("Download error", result[0])
        self.assertEqual(result[1], 500)

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file_success(self, mock_async_client):
        mock_response = mock.AsyncMock()
        mock_response.content = b'{"sanitized": {"failure_reasons": ["reason1", "reason2"]}}'
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('test_data_id', 'test_api_key')
        self.assertIn("reason1", result[0])  # Check for failure reasons log

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_handle_no_sanitized_file_error(self, mock_logging):
        with mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient') as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get.side_effect = Exception("API call failed")

            result = await self.api._handle_no_sanitized_file('test_data_id', 'test_api_key')
            self.assertIn("API call failed", result[0])
            self.assertEqual(result[1], 500)

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_parse_sanitized_data(self, mock_logging):
        response = mock.Mock()
        response.content = b'{"sanitized": {"key": "value"}}'
        sanitized_data = self.api._parse_sanitized_data(response)
        self.assertEqual(sanitized_data, {"key": "value"})

    def test_get_failure_reasons(self):
        sanitized_data = {"failure_reasons": ["reason1", "reason2"]}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, ["reason1", "reason2"])

        sanitized_data = {}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, "")

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_reasons(self, mock_logging):
        _, http_status = self.api._log_sanitization_result(["reason1", "reason2"])
        self.assertEqual(http_status, 204)
        mock_logging.info.assert_called_once()

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_no_reasons(self, mock_logging):
        _, http_status = self.api._log_sanitization_result("")
        self.assertEqual(http_status, 204)
        mock_logging.info.assert_called_once_with(mock.ANY)

    @mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        error_message, http_status = self.api._handle_error(Exception("Test error"), 'test_api_key')
        self.assertIn("Test error", error_message["error"])
        self.assertEqual(http_status, 500)
        mock_logging.error.assert_called_once()

if __name__ == '__main__':
    unittest.main()