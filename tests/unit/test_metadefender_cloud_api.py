import unittest
from unittest import mock, IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import httpx
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI


class TestMetaDefenderCloudAPI(IsolatedAsyncioTestCase):

    def setUp(self):
        self.settings = {'scanRule': 'default_rule', 'scanWith': 'mdaas'}
        self.apikey = "test_api_key"
        self.api = MetaDefenderCloudAPI(settings=self.settings, url='http://example.com', apikey='test_api_key')

    def test_get_submit_file_headers(self):
        headers = self.api._get_submit_file_headers('testfile.txt', {})
        self.assertEqual(headers["filename"], "testfile.txt")
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertEqual(headers["rule"], "default_rule")
        self.assertEqual(headers["scanWith"], "mdaas")
        
        with mock.patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging') as mock_logging:
            self.api._get_submit_file_headers('testfile.txt', {})
            mock_logging.debug.assert_called_once()

    def test_get_submit_file_headers_without_scan_with(self):
        # Test without scanWith configuration
        api_without_scan = MetaDefenderCloudAPI(settings={'scanRule': 'default_rule'}, url='http://example.com', apikey='test_api_key')
        headers = api_without_scan._get_submit_file_headers('testfile.txt', {})
        self.assertEqual(headers["filename"], "testfile.txt")
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertEqual(headers["rule"], "default_rule")
        self.assertNotIn("scanWith", headers)

    def test_check_analysis_complete(self):
        json_response_complete = {"sanitized": {"progress_percentage": 100}}
        self.assertTrue(self.api.check_analysis_complete(json_response_complete))

        json_response_incomplete = {"sanitized": {"progress_percentage": 50}}
        self.assertFalse(self.api.check_analysis_complete(json_response_incomplete))

        json_response_empty = {}
        self.assertFalse(self.api.check_analysis_complete(json_response_empty))

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_response(self, mock_logging):
        self.api._log_response({"key": "value"}, 200)
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_unauthorized(self, mock_logging):
        _, status = self.api._handle_unauthorized({"message": "Unauthorized"}, 401)
        self.assertEqual(status, 401)
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_success(self, mock_async_client):
        mock_response = AsyncMock()
        mock_response.content = b'Test sanitized file content'
        mock_response.status_code = 200
        mock_async_client.return_value.__aenter__.return_value.get.return_value = mock_response

        content, status = await self.api._download_sanitized_file('http://example.com/sanitized_file', 'test_api_key')
        self.assertEqual(content, b'Test sanitized file content')
        self.assertEqual(status, 200)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_error(self, mock_async_client):
        mock_async_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download error")

        result = await self.api._download_sanitized_file('http://example.com/sanitized_file', 'test_api_key')
        self.assertEqual(result[1], 500)
        self.assertIn('error', result[0])
        self.assertIn('Download error', result[0]['error'])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_handle_no_sanitized_file_error(self, mock_logging):
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient') as mock_async_client:
            mock_async_client.return_value.__aenter__.return_value.get.side_effect = Exception("API call failed")

            result = await self.api._handle_no_sanitized_file('test_data_id', 'test_api_key')
            self.assertIn('API call failed', result[0]['error'])
            self.assertEqual(result[1], 500)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_parse_sanitized_data(self, mock_logging):
        response = Mock()
        response.content = b'{"sanitized": {"key": "value"}}'
        sanitized_data = self.api._parse_sanitized_data(response)
        self.assertEqual(sanitized_data, {"key": "value"})

    def test_get_failure_reasons(self):
        sanitized_data = {"failure_reasons": ["reason1", "reason2"]}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, ["reason1", "reason2"])

        sanitized_data_empty = {}
        result = self.api._get_failure_reasons(sanitized_data_empty)
        self.assertEqual(result, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_reasons(self, mock_logging):
        _, http_status = self.api._log_sanitization_result(["reason1", "reason2"])
        self.assertEqual(http_status, 204)
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_no_reasons(self, mock_logging):
        _, http_status = self.api._log_sanitization_result("")
        self.assertEqual(http_status, 204)
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        error_message, http_status = self.api._handle_error(Exception("Test error"), 'test_api_key')
        self.assertIn("Test error", error_message["error"])
        self.assertEqual(http_status, 500)
        mock_logging.error.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_retrieve_sanitized_file_success(self, mock_client):
        data_id = "test123"
        apikey = "test-apikey"
        ip = "127.0.0.1"
        mock_response = MagicMock()
        mock_response.content = b"test content"
        mock_response.status_code = 200
        
        self.api._request_as_json_status = AsyncMock(
            return_value=({"sanitizedFilePath": "http://test.com/file.pdf"}, 200)
        )
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result, status = await self.api.retrieve_sanitized_file(data_id, apikey, ip)
        self.assertEqual(result, b"test content")
        self.assertEqual(status, 200)
        self.api._request_as_json_status.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_retrieve_sanitized_file_no_path(self, mock_client):
        data_id = "test123"
        apikey = "test-apikey"
        ip = "127.0.0.1"
        self.api._request_as_json_status = AsyncMock(
            return_value=({"message": "No path available"}, 200)
        )

        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "sanitized": {
                "failure_reasons": ["File type not supported"]
            }
        }).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        result, status = await self.api.retrieve_sanitized_file(data_id, apikey, ip)
        self.assertEqual(status, 204)
        self.assertEqual(result, "")

if __name__ == '__main__':
    unittest.main()