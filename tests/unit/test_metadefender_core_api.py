import unittest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import json
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.api.log_types import SERVICE


class TestMetaDefenderCoreAPI(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.settings = {
            'headers_engines_metadata': 'some_metadata',
            'fallbackToOriginal': True,
            'scanRule': 'default_rule'
        }
        self.url = "https://test-server.com"
        self.apikey = "test_api_key"
        self.api = MetaDefenderCoreAPI(self.settings, self.url, self.apikey)

    def test_init(self):
        self.assertEqual(self.api.service_name, SERVICE.MetaDefenderCore)
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(self.api.report_url, "https://test-server.com/#/public/process/dataId/{data_id}")
        
        self.assertEqual(self.api.api_endpoints['file_submit']['endpoint'], '/file')
        self.assertEqual(self.api.api_endpoints['check_result']['endpoint'], '/file/{data_id}')
        self.assertEqual(self.api.api_endpoints['hash_lookup']['endpoint'], '/hash/{hash}')
        self.assertEqual(self.api.api_endpoints['sanitized_file']['endpoint'], '/file/converted/{data_id}')

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_hash(self, mock_get_client):
        test_cases = [
            ("abc123", {"hash": "abc123", "status": "clean"}, 200, {"sha256": "abc123", "hash": "abc123", "status": "clean"}),
            ("unknown-hash", {"file_id": "Not Found", "hash_info": "Not Found"}, 404, {"sha256": "unknown-hash"}),
            ("abc123", {"hash": "abc123", "lookup_results": "Not Found"}, 404, {"sha256": "abc123"})
        ]
        
        for hash_value, response_data, expected_status, expected_response in test_cases:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.headers.get.return_value = 'application/json'
            mock_response.json.return_value = response_data
            
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client
            
            json_response, http_status = await self.api.check_hash(hash_value, "api-key", "192.168.1.1")
            
            self.assertEqual(http_status, expected_status)
            self.assertEqual(json_response, expected_response)

    def test_get_submit_file_headers(self):
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
        self.assertNotIn('content-length', json.loads(headers['metadata']))

    def test_get_submit_file_headers_edge_cases(self):
        api_no_rule = MetaDefenderCoreAPI(
            settings={'headers_engines_metadata': 'meta', 'fallbackToOriginal': False, 'scanRule': ''},
            url=self.url,
            apikey=self.apikey
        )
        
        headers_without_ip = self.api._get_submit_file_headers({'filename': "test.txt"}, 'api-key', None)
        self.assertNotIn('x-forwarded-for', headers_without_ip)
        self.assertNotIn('x-real-ip', headers_without_ip)
        
        headers_no_rule = api_no_rule._get_submit_file_headers({'filename': "doc.docx"}, 'key', None)
        self.assertNotIn('rule', headers_no_rule)
        
        headers_no_filename = self.api._get_submit_file_headers({'custom-field': 'value'}, 'key', None)
        self.assertNotIn('filename', headers_no_filename)
        
        headers_default_length = self.api._get_submit_file_headers({'filename': "test.txt"}, 'key', None)
        self.assertEqual(headers_default_length['Content-Length'], '0')
        
        headers_special_chars = self.api._get_submit_file_headers({'filename': "test file with spaces.pdf"}, 'key', None)
        self.assertEqual(headers_special_chars['filename'], 'test%20file%20with%20spaces.pdf')
        
        headers_list_format = self.api._get_submit_file_headers({'filename': "[b'encoded_file.pdf']"}, 'key', None)
        self.assertEqual(headers_list_format['filename'], 'encoded_file.pdf')
        
        headers_filters_none = self.api._get_submit_file_headers({'filename': None}, 'key', None)
        self.assertNotIn('filename', headers_filters_none)

    def test_get_sanitized_file_path(self):
        test_cases = [
            ({
                'data_id': 'test-id-123',
                'process_info': {
                    'post_processing': {
                        'actions_ran': ['Sanitized', 'PasswordProtected']
                    }
                }
            }, 'https://test-server.com/file/converted/test-id-123'),
            ({
                'data_id': 'test-id',
                'process_info': {
                    'post_processing': {
                        'actions_ran': ['OtherAction']
                    }
                }
            }, ''),
            ({'data_id': 'test-id'}, ''),
            ({
                'data_id': 'test-id',
                'process_info': {}
            }, ''),
            ({
                'data_id': 'test-id',
                'process_info': {
                    'post_processing': {
                        'actions_ran': []
                    }
                }
            }, '')
        ]
        
        for json_response, expected_path in test_cases:
            path = self.api.get_sanitized_file_path(json_response)
            self.assertEqual(path, expected_path)

    def test_check_analysis_complete(self):
        self.assertTrue(self.api.check_analysis_complete({"process_info": {"progress_percentage": 100}}))
        self.assertFalse(self.api.check_analysis_complete({"process_info": {"progress_percentage": 50}}))
        self.assertFalse(self.api.check_analysis_complete({"process_info": {"progress_percentage": 0}}))
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging') as mock_logging:
            test_cases = [
                {"data_id": "test-id"},
                {"process_info": {"status": "processing"}},
                {}
            ]
            
            for json_response in test_cases:
                result = self.api.check_analysis_complete(json_response)
                self.assertFalse(result)
            
            self.assertEqual(mock_logging.error.call_count, 3)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file(self, mock_get_client):
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.content = b"sanitized file content"
        
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        mock_response_200_no_ip = MagicMock()
        mock_response_200_no_ip.status_code = 200
        
        mock_client = AsyncMock()
        mock_client.build_request = Mock(return_value="mock_request")
        mock_client.send = AsyncMock(side_effect=[mock_response_success, mock_response_404, mock_response_200_no_ip])
        mock_get_client.return_value = mock_client
        
        with patch('metadefender_menlo.api.metadefender.metadefender_core_api.logging'):
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key", "192.168.1.1")
            self.assertEqual(http_status, 200)
            self.assertEqual(resp, mock_response_success)
            self.assertEqual(client, mock_client)
            
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key", "192.168.1.1")
            self.assertEqual(http_status, 204)
            
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key")
            self.assertEqual(http_status, 200)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_fallback_scenarios(self, mock_get_client):
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
            resp, http_status, client = await self.api.sanitized_file("test-data-id", "api-key", "192.168.1.1")
            self.assertEqual(http_status, 204)
            
            resp, http_status, client = await api_no_fallback.sanitized_file("test-data-id", "api-key", "192.168.1.1")
            self.assertEqual(http_status, 404)

    async def test_extract_filename_from_headers(self):
        test_cases = [
            ({'content-disposition': 'attachment; filename="test_document.pdf"'}, 'test_document.pdf'),
            ({'content-disposition': 'attachment; filename="test%20file.pdf"'}, 'test file.pdf'),
            ({'content-disposition': 'attachment; filename=document.txt'}, 'document.txt'),
            ({'content-disposition': 'inline; creation-date="2023-01-01"; filename="report.xlsx"'}, 'report.xlsx'),
            ({'content-disposition': 'attachment'}, None),
            ({}, None),
            (None, None)
        ]
        
        for response_headers, expected_filename in test_cases:
            filename = await self.api._extract_filename_from_headers(response_headers)
            self.assertEqual(filename, expected_filename)

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


if __name__ == '__main__':
    unittest.main()