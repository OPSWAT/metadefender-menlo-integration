import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE


class TestMetaDefenderCloudAPI(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
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
        self.assertEqual(self.api.service_name, SERVICE.meta_defender_cloud)
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.server_url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(
            self.api.report_url,
            "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"
        )

    def test_get_submit_file_headers(self):
        metadata = {
            'filename': "test_file.pdf",
            'content-type': 'application/pdf',
            'custom-header': 'custom-value'
        }
        headers = self.api._get_submit_file_headers(metadata, 'api-key-123', '192.168.1.1')
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['rule'], 'default_rule')
        self.assertEqual(headers['apikey'], 'api-key-123')
        self.assertEqual(headers['x-forwarded-for'], '192.168.1.1')
        self.assertEqual(headers['x-real-ip'], '192.168.1.1')
        self.assertEqual(headers['filename'], 'test_file.pdf')
        self.assertEqual(headers['scanWith'], 'mdaas')
        self.assertEqual(headers['custom-header'], 'custom-value')

    def test_get_submit_file_headers_edge_cases(self):
        api_no_scan = MetaDefenderCloudAPI(
            settings={'scanRule': 'rule1', 'headers_scan_with': ''},
            url=self.server_url,
            apikey=self.apikey
        )
        
        headers_without_ip = self.api._get_submit_file_headers({'filename': "test.txt"}, 'api-key', None)
        self.assertNotIn('x-forwarded-for', headers_without_ip)
        self.assertNotIn('x-real-ip', headers_without_ip)
        
        headers_no_scan = api_no_scan._get_submit_file_headers({'filename': "doc.docx"}, 'key', '10.0.0.1')
        self.assertNotIn('scanWith', headers_no_scan)
        
        headers_special_chars = self.api._get_submit_file_headers({'filename': "test file with spaces.pdf"}, 'key', None)
        self.assertEqual(headers_special_chars['filename'], 'test%20file%20with%20spaces.pdf')
        
        headers_list_format = self.api._get_submit_file_headers({'filename': "[b'encoded_file.pdf']"}, 'key', None)
        self.assertEqual(headers_list_format['filename'], 'encoded_file.pdf')
        
        headers_filters_none = self.api._get_submit_file_headers({'filename': "test.txt", 'null-field': None}, 'key', None)
        self.assertNotIn('null-field', headers_filters_none)

    def test_get_sanitized_file_path(self):
        self.assertEqual(
            self.api.get_sanitized_file_path({'sanitized': {'file_path': 'https://cdn.metadefender.com/sanitized/file123.pdf'}}),
            'https://cdn.metadefender.com/sanitized/file123.pdf'
        )
        self.assertEqual(self.api.get_sanitized_file_path({'data_id': 'test123'}), '')
        self.assertEqual(self.api.get_sanitized_file_path({'sanitized': {'status': 'completed'}}), '')
        self.assertEqual(self.api.get_sanitized_file_path({}), '')

    def test_check_analysis_complete(self):
        self.assertTrue(self.api.check_analysis_complete({'sanitized': {'progress_percentage': 100}}))
        self.assertFalse(self.api.check_analysis_complete({'sanitized': {'progress_percentage': 75}}))
        self.assertFalse(self.api.check_analysis_complete({'sanitized': {'progress_percentage': 0}}))
        
        with patch('builtins.print') as mock_print:
            self.assertFalse(self.api.check_analysis_complete({'data_id': 'test123'}))
            self.assertFalse(self.api.check_analysis_complete({'sanitized': {'status': 'processing'}}))
            self.assertFalse(self.api.check_analysis_complete({}))
            self.assertEqual(mock_print.call_count, 3)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_success(self, mock_get_client):
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

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_unauthorized(self, mock_get_client):
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
    async def test_sanitized_file_404_scenarios(self, mock_get_client):
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
        
        _, status_with_fallback, _ = await api_with_fallback.sanitized_file("data-id", "key", "1.1.1.1")
        _, status_without_fallback, _ = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
        
        self.assertEqual(status_with_fallback, 204)
        self.assertEqual(status_without_fallback, 404)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_no_url_scenarios(self, mock_get_client):
        test_cases = [
            ({"message": "No sanitized file"}, {"sanitized": {"failure_reasons": ["File type not supported"]}}),
            ({}, {"sanitized": {"reason": "Not available"}}),
            ({}, {"sanitized": {}})
        ]
        
        for json_response, detail_response in test_cases:
            mock_json_response = MagicMock()
            mock_json_response.status_code = 200
            mock_json_response.headers.get.return_value = 'application/json'
            mock_json_response.json.return_value = json_response
            
            mock_detail_response = MagicMock()
            mock_detail_response.json.return_value = detail_response
            
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=[mock_json_response, mock_detail_response])
            mock_get_client.return_value = mock_client
            
            with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
                _, http_status, _ = await self.api.sanitized_file("data-id", "key", "1.1.1.1")
                self.assertEqual(http_status, 204)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_download_sanitized_file(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.content = b"Downloaded file content"
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            content, status = await self.api._download_sanitized_file("https://cdn.example.com/file.pdf", "api-key")
        
        self.assertEqual(content, b"Downloaded file content")
        self.assertEqual(status, 200)
        
        mock_client.get = AsyncMock(side_effect=Exception("Network error"))
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status = await self.api._download_sanitized_file("https://cdn.example.com/file.pdf", "api-key")
        
        self.assertEqual(status, 500)
        self.assertIn("error", result)
        self.assertIn("Network error", result["error"])

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_handle_no_sanitized_file(self, mock_get_client):
        test_cases = [
            ({"sanitized": {"failure_reasons": ["File type not supported"]}}, True),
            ({"sanitized": {"reason": "Sanitization not available"}}, False),
            ({"sanitized": {}}, False)
        ]
        
        for response_data, has_failure_reasons in test_cases:
            mock_response = MagicMock()
            mock_response.json.return_value = response_data
            
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging') as mock_log:
                result, status, client = await self.api._handle_no_sanitized_file("data-id", "api-key")
                self.assertEqual(status, 204)
                self.assertIsNone(result)
                self.assertIsNone(client)
                self.assertTrue(mock_log.info.called)
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("API error"))
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging'):
            result, status = await self.api._handle_no_sanitized_file("data-id", "api-key")
        
        self.assertEqual(status, 500)
        self.assertIn("error", result)
        self.assertIn("API error", result["error"])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result(self, mock_logging):
        test_cases = [
            (["Reason 1", "Reason 2"], "Sanitization failed with failure reasons"),
            ("", "Sanitized file not available"),
            ([], "Sanitized file not available"),
            (None, "Sanitized file not available")
        ]
        
        for failure_reasons, expected_message in test_cases:
            result, status, client = self.api._log_sanitization_result(failure_reasons)
            self.assertEqual(status, 204)
            self.assertIsNone(result)
            self.assertIsNone(client)
            mock_logging.info.assert_called()
            
            call_args = mock_logging.info.call_args[0]
            self.assertIn(expected_message, call_args[0])

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        errors = [
            Exception("Test error message"),
            ValueError("Invalid value"),
            KeyError("Missing key"),
            RuntimeError("Runtime issue")
        ]
        
        for error in errors:
            result, status = self.api._handle_error(error, "api-key-123")
            self.assertEqual(status, 500)
            self.assertIn("error", result)
            self.assertIn(str(error), result["error"])
            mock_logging.error.assert_called()

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_inherited_methods(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data_id": "test-id", "status": "queued"}
        mock_response.headers.get.return_value = 'application/json'
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        file_bytes = Mock()
        metadata = {'filename': "test.pdf"}
        
        json_response, status = await self.api.submit(file_bytes, metadata, "api-key", "192.168.1.1")
        self.assertEqual(status, 200)
        self.assertEqual(json_response["data_id"], "test-id")
        
        json_response, status = await self.api.check_result("data-id", "api-key", "192.168.1.1")
        self.assertEqual(status, 200)
        self.assertIn("data_id", json_response)
        
        json_response, status = await self.api.check_hash("abc123", "api-key", "192.168.1.1")
        self.assertEqual(status, 200)
        self.assertEqual(json_response["sha256"], "abc123")


if __name__ == '__main__':
    unittest.main()