import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE


class TestMetaDefenderCloudAPI(unittest.IsolatedAsyncioTestCase):
    """Comprehensive test suite for MetaDefenderCloudAPI"""

    def setUp(self):
        """Set up test fixtures"""
        self.settings = {
            'scanRule': 'default_rule',
            'headers_scan_with': 'mdaas',
            'fallbackToOriginal': False
        }
        self.apikey = "test_api_key"
        self.server_url = 'https://api.metadefender.com/v4'
        self.api = MetaDefenderCloudAPI(
            settings=self.settings,
            url=self.server_url,
            apikey=self.apikey
        )

    def test_init(self):
        """Test MetaDefenderCloudAPI initialization"""
        self.assertEqual(self.api.service_name, SERVICE.MetaDefenderCloud)
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.server_url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(
            self.api.report_url,
            "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"
        )

    def test_get_submit_file_headers_with_all_params(self):
        """Test _get_submit_file_headers with all parameters"""
        metadata = {
            'filename': "test_file.pdf",
            'content-type': 'application/pdf'
        }
        headers = self.api._get_submit_file_headers(metadata, 'api-key-123', '192.168.1.1')
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['rule'], 'default_rule')
        self.assertEqual(headers['apikey'], 'api-key-123')
        self.assertEqual(headers['x-forwarded-for'], '192.168.1.1')
        self.assertEqual(headers['x-real-ip'], '192.168.1.1')
        self.assertEqual(headers['filename'], 'test_file.pdf')
        self.assertEqual(headers['scanWith'], 'mdaas')
        self.assertIn('content-type', headers)

    def test_get_submit_file_headers_without_client_ip(self):
        """Test _get_submit_file_headers without client IP"""
        metadata = {'filename': "test.txt"}
        headers = self.api._get_submit_file_headers(metadata, 'api-key', None)
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['apikey'], 'api-key')
        self.assertNotIn('x-forwarded-for', headers)
        self.assertNotIn('x-real-ip', headers)

    def test_get_submit_file_headers_without_scan_with(self):
        """Test _get_submit_file_headers without scanWith configuration"""
        api_no_scan = MetaDefenderCloudAPI(
            settings={'scanRule': 'rule1', 'headers_scan_with': ''},
            url=self.server_url,
            apikey=self.apikey
        )
        metadata = {'filename': "doc.docx"}
        headers = api_no_scan._get_submit_file_headers(metadata, 'key', '10.0.0.1')
        
        self.assertNotIn('scanWith', headers)

    def test_get_submit_file_headers_with_different_scan_with(self):
        """Test _get_submit_file_headers with different scanWith values"""
        api_mdcore = MetaDefenderCloudAPI(
            settings={'scanRule': 'rule1', 'headers_scan_with': 'mdcore'},
            url=self.server_url,
            apikey=self.apikey
        )
        metadata = {'filename': "image.png"}
        headers = api_mdcore._get_submit_file_headers(metadata, 'key', None)
        
        self.assertEqual(headers['scanWith'], 'mdcore')

    def test_get_submit_file_headers_filename_encoding(self):
        """Test _get_submit_file_headers with special characters in filename"""
        metadata = {'filename': "test file with spaces.pdf"}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        # URL encoding should handle spaces
        self.assertEqual(headers['filename'], 'test%20file%20with%20spaces.pdf')

    def test_get_submit_file_headers_filename_as_string_list(self):
        """Test _get_submit_file_headers with filename as string representation of list"""
        # This is the format that comes from URL parameters
        metadata = {'filename': "[b'encoded_file.pdf']"}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        # Should decode the bytes and URL encode
        self.assertEqual(headers['filename'], 'encoded_file.pdf')

    def test_get_submit_file_headers_metadata_merge(self):
        """Test _get_submit_file_headers merges metadata into headers"""
        metadata = {
            'filename': "test.txt",
            'custom-header': 'custom-value',
            'another-field': 'another-value'
        }
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        self.assertEqual(headers['custom-header'], 'custom-value')
        self.assertEqual(headers['another-field'], 'another-value')

    def test_get_submit_file_headers_filters_none_values(self):
        """Test _get_submit_file_headers filters out None values"""
        metadata = {
            'filename': "test.txt",
            'valid-field': 'value',
            'null-field': None
        }
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        self.assertIn('valid-field', headers)
        self.assertNotIn('null-field', headers)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_get_submit_file_headers_logging(self, mock_logging):
        """Test _get_submit_file_headers logs debug information"""
        metadata = {'filename': "test.txt"}
        self.api._get_submit_file_headers(metadata, 'key', None)
        
        mock_logging.debug.assert_called_once()

    def test_get_sanitized_file_path_success(self):
        """Test get_sanitized_file_path with valid response"""
        json_response = {
            'sanitized': {
                'file_path': 'https://cdn.metadefender.com/sanitized/file123.pdf'
            }
        }
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, 'https://cdn.metadefender.com/sanitized/file123.pdf')

    def test_get_sanitized_file_path_missing_sanitized(self):
        """Test get_sanitized_file_path when sanitized key is missing"""
        json_response = {'data_id': 'test123'}
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_get_sanitized_file_path_missing_file_path(self):
        """Test get_sanitized_file_path when file_path is missing"""
        json_response = {'sanitized': {'status': 'completed'}}
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_get_sanitized_file_path_empty_response(self):
        """Test get_sanitized_file_path with empty response"""
        path = self.api.get_sanitized_file_path({})
        
        self.assertEqual(path, '')

    def test_check_analysis_complete_100_percent(self):
        """Test check_analysis_complete with 100% progress"""
        json_response = {
            'sanitized': {
                'progress_percentage': 100
            }
        }
        result = self.api.check_analysis_complete(json_response)
        
        self.assertTrue(result)

    def test_check_analysis_complete_partial(self):
        """Test check_analysis_complete with partial progress"""
        json_response = {
            'sanitized': {
                'progress_percentage': 75
            }
        }
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)

    def test_check_analysis_complete_zero_percent(self):
        """Test check_analysis_complete with 0% progress"""
        json_response = {
            'sanitized': {
                'progress_percentage': 0
            }
        }
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)

    def test_check_analysis_complete_missing_sanitized(self):
        """Test check_analysis_complete when sanitized key is missing"""
        json_response = {'data_id': 'test123'}
        
        # Capture the print statement
        with patch('builtins.print') as mock_print:
            result = self.api.check_analysis_complete(json_response)
            self.assertFalse(result)
            mock_print.assert_called_once()

    def test_check_analysis_complete_missing_progress(self):
        """Test check_analysis_complete when progress_percentage is missing"""
        json_response = {'sanitized': {'status': 'processing'}}
        
        with patch('builtins.print') as mock_print:
            result = self.api.check_analysis_complete(json_response)
            self.assertFalse(result)
            mock_print.assert_called_once()

    def test_check_analysis_complete_empty_response(self):
        """Test check_analysis_complete with empty response"""
        with patch('builtins.print') as mock_print:
            result = self.api.check_analysis_complete({})
            self.assertFalse(result)
            mock_print.assert_called_once()

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_success_with_url(self, mock_get_client):
        """Test sanitized_file when sanitizedFilePath is provided"""
        # Mock the HTTP client responses
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {"sanitizedFilePath": "https://cdn.example.com/file.pdf"}
        
        mock_file_response = MagicMock()
        mock_file_response.status_code = 200
        mock_file_response.content = b"sanitized file content"
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_json_response)
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_file_response)
        mock_get_client.return_value = mock_client
        
        resp, http_status, client = await self.api.sanitized_file("data-id-123", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 200)
        self.assertEqual(resp, mock_file_response)
        self.assertEqual(client, mock_client)
        mock_client.build_request.assert_called_once_with("GET", "https://cdn.example.com/file.pdf")

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_unauthorized(self, mock_get_client):
        """Test sanitized_file with 401 unauthorized response"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {"error": "Unauthorized"}
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        resp, http_status, client = await self.api.sanitized_file("data-id", "bad-key", "1.1.1.1")
        
        self.assertEqual(http_status, 401)
        self.assertEqual(resp, {"error": "Unauthorized"})
        self.assertIsNone(client)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_404_with_fallback(self, mock_get_client):
        """Test sanitized_file with 404 and fallback enabled"""
        api_with_fallback = MetaDefenderCloudAPI(
            settings={'scanRule': 'rule', 'headers_scan_with': '', 'fallbackToOriginal': True},
            url=self.server_url,
            apikey=self.apikey
        )
        
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {"sanitizedFilePath": "https://cdn.example.com/file.pdf"}
        
        mock_file_response = MagicMock()
        mock_file_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_json_response)
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_file_response)
        mock_get_client.return_value = mock_client
        
        resp, http_status, client = await api_with_fallback.sanitized_file("data-id", "key", "1.1.1.1")
        
        self.assertEqual(http_status, 204)  # 404 becomes 204 with fallback

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_404_without_fallback(self, mock_get_client):
        """Test sanitized_file with 404 and no fallback"""
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {"sanitizedFilePath": "https://cdn.example.com/file.pdf"}
        
        mock_file_response = MagicMock()
        mock_file_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_json_response)
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_file_response)
        mock_get_client.return_value = mock_client
        
        resp, http_status, client = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
        
        self.assertEqual(http_status, 404)  # Stays 404 without fallback

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_no_url_with_failure_reasons(self, mock_get_client):
        """Test sanitized_file when no sanitizedFilePath and has failure reasons"""
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {"message": "No sanitized file"}
        
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {
            "sanitized": {
                "failure_reasons": ["File type not supported"]
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_json_response, mock_detail_response])
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
            
            self.assertEqual(http_status, 204)
            self.assertIsNone(resp)
            self.assertIsNone(client)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_no_url_with_reason(self, mock_get_client):
        """Test sanitized_file when no sanitizedFilePath and has reason field"""
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {}
        
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {
            "sanitized": {
                "reason": "Not available"
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_json_response, mock_detail_response])
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
            
            self.assertEqual(http_status, 204)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_no_url_no_reasons(self, mock_get_client):
        """Test sanitized_file when no sanitizedFilePath and no failure reasons"""
        mock_json_response = MagicMock()
        mock_json_response.status_code = 200
        mock_json_response.headers.get.return_value = 'application/json'
        mock_json_response.json.return_value = {}
        
        mock_detail_response = MagicMock()
        mock_detail_response.json.return_value = {"sanitized": {}}
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=[mock_json_response, mock_detail_response])
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
            
            self.assertEqual(http_status, 204)
            self.assertIsNone(resp)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_download_sanitized_file_success(self, mock_get_client):
        """Test _download_sanitized_file with successful download"""
        mock_response = MagicMock()
        mock_response.content = b"Downloaded file content"
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            content, status = await self.api._download_sanitized_file(
                "https://cdn.example.com/file.pdf",
                "api-key"
            )
        
        self.assertEqual(content, b"Downloaded file content")
        self.assertEqual(status, 200)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_download_sanitized_file_error(self, mock_get_client):
        """Test _download_sanitized_file with error"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status = await self.api._download_sanitized_file(
                "https://cdn.example.com/file.pdf",
                "api-key"
            )
        
        self.assertEqual(status, 500)
        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_handle_no_sanitized_file_with_failure_reasons(self, mock_get_client):
        """Test _handle_no_sanitized_file when failure reasons are provided"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sanitized": {
                "failure_reasons": ["File type not supported", "File too large"]
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging') as mock_log:
            result, status, client = await self.api._handle_no_sanitized_file("data-id", "api-key")
            
            self.assertEqual(status, 204)
            self.assertIsNone(result)
            self.assertIsNone(client)
            # Verify logging was called
            self.assertTrue(mock_log.info.called)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_handle_no_sanitized_file_with_reason(self, mock_get_client):
        """Test _handle_no_sanitized_file when reason (not failure_reasons) is provided"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sanitized": {
                "reason": "Sanitization not available"
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status, client = await self.api._handle_no_sanitized_file("data-id", "api-key")
            
            self.assertEqual(status, 204)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_handle_no_sanitized_file_no_reasons(self, mock_get_client):
        """Test _handle_no_sanitized_file when no failure reasons are provided"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "sanitized": {}
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status, client = await self.api._handle_no_sanitized_file("data-id", "api-key")
            
            self.assertEqual(status, 204)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_handle_no_sanitized_file_error(self, mock_get_client):
        """Test _handle_no_sanitized_file with error"""
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status = await self.api._handle_no_sanitized_file("data-id", "api-key")
        
        self.assertEqual(status, 500)
        self.assertIn("error", result)
        self.assertIn("API error", result["error"])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_failure_reasons(self, mock_logging):
        """Test _log_sanitization_result with failure reasons"""
        failure_reasons = ["Reason 1", "Reason 2"]
        result, status, client = self.api._log_sanitization_result(failure_reasons)
        
        self.assertEqual(status, 204)
        self.assertIsNone(result)
        self.assertIsNone(client)
        mock_logging.info.assert_called_once()
        
        # Verify the log message contains failure reasons
        call_args = mock_logging.info.call_args[0]
        self.assertIn("Sanitization failed with failure reasons", call_args[0])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_without_failure_reasons(self, mock_logging):
        """Test _log_sanitization_result without failure reasons"""
        result, status, client = self.api._log_sanitization_result("")
        
        self.assertEqual(status, 204)
        self.assertIsNone(result)
        self.assertIsNone(client)
        mock_logging.info.assert_called_once()
        
        # Verify the log message indicates no sanitized file
        call_args = mock_logging.info.call_args[0]
        self.assertIn("Sanitized file not available", call_args[0])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_empty_list(self, mock_logging):
        """Test _log_sanitization_result with empty list"""
        result, status, client = self.api._log_sanitization_result([])
        
        self.assertEqual(status, 204)
        self.assertIsNone(result)
        self.assertIsNone(client)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_none(self, mock_logging):
        """Test _log_sanitization_result with None"""
        result, status, client = self.api._log_sanitization_result(None)
        
        self.assertEqual(status, 204)
        self.assertIsNone(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error_with_exception(self, mock_logging):
        """Test _handle_error with exception"""
        error = Exception("Test error message")
        result, status = self.api._handle_error(error, "api-key-123")
        
        self.assertEqual(status, 500)
        self.assertIn("error", result)
        self.assertIn("Test error message", result["error"])
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error_with_different_exceptions(self, mock_logging):
        """Test _handle_error with different exception types"""
        errors = [
            ValueError("Invalid value"),
            KeyError("Missing key"),
            RuntimeError("Runtime issue")
        ]
        
        for error in errors:
            result, status = self.api._handle_error(error, "key")
            self.assertEqual(status, 500)
            self.assertIn(str(error), result["error"])

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_inherited_submit_method(self, mock_get_client):
        """Test that inherited submit method works correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data_id": "test-id", "status": "queued"}
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        file_bytes = Mock()
        metadata = {'filename': "test.pdf"}
        
        json_response, status = await self.api.submit(file_bytes, metadata, "api-key", "192.168.1.1")
        
        self.assertEqual(status, 200)
        self.assertEqual(json_response["data_id"], "test-id")

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_inherited_check_result_method(self, mock_get_client):
        """Test that inherited check_result method works correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "sanitized": {"progress_percentage": 100}
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, status = await self.api.check_result("data-id", "api-key", "192.168.1.1")
        
        self.assertEqual(status, 200)
        self.assertIn("sanitized", json_response)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_inherited_check_hash_method(self, mock_get_client):
        """Test that inherited check_hash method works correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {"hash": "abc123", "status": "found"}
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, status = await self.api.check_hash("abc123", "api-key", "192.168.1.1")
        
        self.assertEqual(status, 200)
        self.assertEqual(json_response["sha256"], "abc123")


if __name__ == '__main__':
    unittest.main()
