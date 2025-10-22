import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.api.log_types import SERVICE


class TestMetaDefenderCoreAPI(unittest.IsolatedAsyncioTestCase):
    """Comprehensive test suite for MetaDefenderCoreAPI"""

    def setUp(self):
        """Set up test fixtures"""
        self.settings = {
            'headers_engines_metadata': 'some_metadata',
            'fallbackToOriginal': True,
            'scanRule': 'default_rule'
        }
        self.url = "https://test-server.com"
        self.apikey = "test_api_key"
        self.api = MetaDefenderCoreAPI(self.settings, self.url, self.apikey)

    def test_init(self):
        """Test MetaDefenderCoreAPI initialization"""
        self.assertEqual(self.api.service_name, SERVICE.MetaDefenderCore)
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(self.api.report_url, "https://test-server.com/#/public/process/dataId/{data_id}")
        
        # Verify API endpoints
        self.assertEqual(self.api.api_endpoints['file_submit']['endpoint'], '/file')
        self.assertEqual(self.api.api_endpoints['check_result']['endpoint'], '/file/{data_id}')
        self.assertEqual(self.api.api_endpoints['hash_lookup']['endpoint'], '/hash/{hash}')
        self.assertEqual(self.api.api_endpoints['sanitized_file']['endpoint'], '/file/converted/{data_id}')

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_hash_success(self, mock_get_client):
        """Test check_hash with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "hash": "abc123",
            "status": "clean"
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, http_status = await self.api.check_hash("abc123", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 200)
        self.assertEqual(json_response['sha256'], 'abc123')
        self.assertEqual(json_response['hash'], 'abc123')

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_hash_not_found(self, mock_get_client):
        """Test check_hash with 'Not Found' response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "file_id": "Not Found",
            "hash_info": "Not Found"
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, http_status = await self.api.check_hash("unknown-hash", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 404)
        self.assertEqual(json_response, {"sha256": "unknown-hash"})

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_hash_partial_not_found(self, mock_get_client):
        """Test check_hash with partial 'Not Found' in values"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "hash": "abc123",
            "lookup_results": "Not Found"
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, http_status = await self.api.check_hash("abc123", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 404)
        self.assertEqual(json_response, {"sha256": "abc123"})

    def test_get_submit_file_headers_with_all_params(self):
        """Test _get_submit_file_headers with all parameters"""
        metadata = {
            'filename': "test_file.pdf",
            'content-length': '12345',
            'custom-field': 'custom-value'
        }
        headers = self.api._get_submit_file_headers(metadata, 'api-key-123', '192.168.1.1')
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['Content-Length'], '12345')
        self.assertEqual(headers['apikey'], 'api-key-123')
        self.assertEqual(headers['x-forwarded-for'], '192.168.1.1')
        self.assertEqual(headers['x-real-ip'], '192.168.1.1')
        self.assertEqual(headers['filename'], 'test_file.pdf')
        self.assertEqual(headers['rule'], 'default_rule')
        self.assertEqual(headers['engines-metadata'], 'some_metadata')
        self.assertIn('metadata', headers)
        # content-length should be removed from metadata
        self.assertNotIn('content-length', json.loads(headers['metadata']))

    def test_get_submit_file_headers_without_client_ip(self):
        """Test _get_submit_file_headers without client IP"""
        metadata = {'filename': "test.txt"}
        headers = self.api._get_submit_file_headers(metadata, 'api-key', None)
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['apikey'], 'api-key')
        self.assertNotIn('x-forwarded-for', headers)
        self.assertNotIn('x-real-ip', headers)

    def test_get_submit_file_headers_without_scan_rule(self):
        """Test _get_submit_file_headers without scan rule"""
        api_no_rule = MetaDefenderCoreAPI(
            settings={'headers_engines_metadata': 'meta', 'fallbackToOriginal': False, 'scanRule': ''},
            url=self.url,
            apikey=self.apikey
        )
        metadata = {'filename': "doc.docx"}
        headers = api_no_rule._get_submit_file_headers(metadata, 'key', None)
        
        self.assertNotIn('rule', headers)

    def test_get_submit_file_headers_without_filename(self):
        """Test _get_submit_file_headers without filename in metadata"""
        metadata = {'custom-field': 'value'}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        # Should not have filename header when metadata doesn't have filename
        self.assertNotIn('filename', headers)

    def test_get_submit_file_headers_content_length_default(self):
        """Test _get_submit_file_headers defaults content-length to 0"""
        metadata = {'filename': "test.txt"}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        self.assertEqual(headers['Content-Length'], '0')

    def test_get_submit_file_headers_content_length_removed_from_metadata(self):
        """Test that content-length is removed from metadata dict"""
        metadata = {
            'filename': "test.txt",
            'content-length': '500',
            'other-field': 'value'
        }
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        # content-length should be in header
        self.assertEqual(headers['Content-Length'], '500')
        # but not in metadata JSON
        metadata_dict = json.loads(headers['metadata'])
        self.assertNotIn('content-length', metadata_dict)
        self.assertIn('other-field', metadata_dict)

    def test_get_submit_file_headers_filename_encoding(self):
        """Test _get_submit_file_headers URL encodes filename"""
        metadata = {'filename': "test file with spaces.pdf"}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        self.assertEqual(headers['filename'], 'test%20file%20with%20spaces.pdf')

    def test_get_submit_file_headers_filename_as_string_list(self):
        """Test _get_submit_file_headers with filename as string representation"""
        metadata = {'filename': "[b'encoded_file.pdf']"}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        self.assertEqual(headers['filename'], 'encoded_file.pdf')

    def test_get_submit_file_headers_filters_none_values(self):
        """Test _get_submit_file_headers filters out None values"""
        metadata = {'filename': None}
        headers = self.api._get_submit_file_headers(metadata, 'key', None)
        
        # None values should be filtered out
        self.assertNotIn('filename', headers)

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging')
    def test_get_submit_file_headers_logging(self, mock_logging):
        """Test _get_submit_file_headers logs debug information"""
        metadata = {'filename': "test.txt"}
        self.api._get_submit_file_headers(metadata, 'key', None)
        
        mock_logging.debug.assert_called_once()

    def test_get_sanitized_file_path_success(self):
        """Test get_sanitized_file_path with valid response"""
        json_response = {
            'data_id': 'test-id-123',
            'process_info': {
                'post_processing': {
                    'actions_ran': ['Sanitized', 'PasswordProtected']
                }
            }
        }
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, 'https://test-server.com/file/converted/test-id-123')

    def test_get_sanitized_file_path_not_sanitized(self):
        """Test get_sanitized_file_path when file was not sanitized"""
        json_response = {
            'data_id': 'test-id',
            'process_info': {
                'post_processing': {
                    'actions_ran': ['OtherAction']
                }
            }
        }
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_get_sanitized_file_path_missing_process_info(self):
        """Test get_sanitized_file_path when process_info is missing"""
        json_response = {'data_id': 'test-id'}
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_get_sanitized_file_path_missing_post_processing(self):
        """Test get_sanitized_file_path when post_processing is missing"""
        json_response = {
            'data_id': 'test-id',
            'process_info': {}
        }
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_get_sanitized_file_path_empty_actions_ran(self):
        """Test get_sanitized_file_path with empty actions_ran"""
        json_response = {
            'data_id': 'test-id',
            'process_info': {
                'post_processing': {
                    'actions_ran': []
                }
            }
        }
        path = self.api.get_sanitized_file_path(json_response)
        
        self.assertEqual(path, '')

    def test_check_analysis_complete_success(self):
        """Test check_analysis_complete with 100% progress"""
        json_response = {"process_info": {"progress_percentage": 100}}
        result = self.api.check_analysis_complete(json_response)
        
        self.assertTrue(result)

    def test_check_analysis_complete_incomplete(self):
        """Test check_analysis_complete with partial progress"""
        json_response = {"process_info": {"progress_percentage": 50}}
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)

    def test_check_analysis_complete_zero_percent(self):
        """Test check_analysis_complete with 0% progress"""
        json_response = {"process_info": {"progress_percentage": 0}}
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging')
    def test_check_analysis_complete_missing_process_info(self, mock_logging):
        """Test check_analysis_complete when process_info is missing"""
        json_response = {"data_id": "test-id"}
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging')
    def test_check_analysis_complete_missing_progress(self, mock_logging):
        """Test check_analysis_complete when progress_percentage is missing"""
        json_response = {"process_info": {"status": "processing"}}
        result = self.api.check_analysis_complete(json_response)
        
        self.assertFalse(result)
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging')
    def test_check_analysis_complete_empty_response(self, mock_logging):
        """Test check_analysis_complete with empty response"""
        result = self.api.check_analysis_complete({})
        
        self.assertFalse(result)
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_success(self, mock_get_client):
        """Test sanitized_file with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"sanitized file content"
        
        mock_client = AsyncMock()
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 200)
        self.assertEqual(resp, mock_response)
        self.assertEqual(client, mock_client)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_404_with_fallback(self, mock_get_client):
        """Test sanitized_file with 404 and fallback enabled"""
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 204)  # 404 becomes 204 with fallback

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_404_without_fallback(self, mock_get_client):
        """Test sanitized_file with 404 and no fallback"""
        api_no_fallback = MetaDefenderCoreAPI(
            settings={'headers_engines_metadata': 'meta', 'fallbackToOriginal': False, 'scanRule': ''},
            url=self.url,
            apikey=self.apikey
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 404
        
        mock_client = AsyncMock()
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging'):
            resp, http_status, client = await api_no_fallback.sanitized_file("test-data-id", "api-key", "192.168.1.1")
        
        self.assertEqual(http_status, 404)  # Stays 404 without fallback

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_without_ip(self, mock_get_client):
        """Test sanitized_file without IP address"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key")
        
        self.assertEqual(http_status, 200)

    async def test_extract_filename_from_headers_with_quotes(self):
        """Test _extract_filename_from_headers with quoted filename"""
        response_headers = {
            'content-disposition': 'attachment; filename="test_document.pdf"'
        }
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertEqual(filename, 'test_document.pdf')

    async def test_extract_filename_from_headers_with_url_encoding(self):
        """Test _extract_filename_from_headers with URL-encoded filename"""
        response_headers = {
            'content-disposition': 'attachment; filename="test%20file.pdf"'
        }
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertEqual(filename, 'test file.pdf')

    async def test_extract_filename_from_headers_without_quotes(self):
        """Test _extract_filename_from_headers with filename without quotes"""
        response_headers = {
            'content-disposition': 'attachment; filename=document.txt'
        }
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertEqual(filename, 'document.txt')

    async def test_extract_filename_from_headers_complex_disposition(self):
        """Test _extract_filename_from_headers with complex content-disposition"""
        response_headers = {
            'content-disposition': 'inline; creation-date="2023-01-01"; filename="report.xlsx"'
        }
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertEqual(filename, 'report.xlsx')

    async def test_extract_filename_from_headers_no_filename(self):
        """Test _extract_filename_from_headers when filename is not present"""
        response_headers = {
            'content-disposition': 'attachment'
        }
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertIsNone(filename)

    async def test_extract_filename_from_headers_missing_disposition(self):
        """Test _extract_filename_from_headers when content-disposition is missing"""
        response_headers = {}
        filename = await self.api._extract_filename_from_headers(response_headers)
        
        self.assertIsNone(filename)

    async def test_extract_filename_from_headers_error_handling(self):
        """Test _extract_filename_from_headers error handling"""
        # Pass non-dict to trigger exception
        filename = await self.api._extract_filename_from_headers(None)
        
        self.assertIsNone(filename)

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
            "process_info": {"progress_percentage": 100}
        }
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        json_response, status = await self.api.check_result("data-id", "api-key", "192.168.1.1")
        
        self.assertEqual(status, 200)
        self.assertIn("process_info", json_response)


if __name__ == '__main__':
    unittest.main()
