import unittest
from unittest.mock import patch, AsyncMock, MagicMock, Mock
import json
from httpx import HTTPError
import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE


class MetaDefenderAPIImpl(MetaDefenderAPI):
    def __init__(self, settings, url, apikey):
        super().__init__(settings, url, apikey)
        self.service_name = SERVICE.meta_defender_core

    def _get_submit_file_headers(self, metadata, apikey, ip):
        headers = {
            'Content-Type': 'application/octet-stream',
            'apikey': apikey
        }
        if ip:
            headers['x-forwarded-for'] = ip
            headers['x-real-ip'] = ip
        return headers

    def check_analysis_complete(self, json_response):
        if "process_info" in json_response and "progress_percentage" in json_response["process_info"]:
            return json_response["process_info"]["progress_percentage"] == 100
        return False

    def get_sanitized_file_path(self, json_response):
        try:
            if "Sanitized" in json_response.get('process_info', {}).get('post_processing', {}).get('actions_ran', []):
                data_id = json_response['data_id']
                return f"{self.server_url}/file/converted/{data_id}"
        except Exception:
            return ''
        return ''

    async def sanitized_file(self, data_id, apikey, ip=""):
        headers = {
            'apikey': apikey,
            'x-forwarded-for': ip,
            'x-real-ip': ip,
            'User-Agent': 'MenloTornadoIntegration'
        }
        return await self._request_as_json_status("sanitized_file", fields={"data_id": data_id}, headers=headers)


class MetaDefenderAPITest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.settings = {
            'headers_scan_with': '',
            'scanRule': 'default',
            'headers_engines_metadata': '',
            'fallbackToOriginal': False
        }
        self.api = MetaDefenderAPIImpl(self.settings, "https://mock-url.com", "mock-api-key")

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_submit_scenarios(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data_id": "test-data-id", "status": "submitted"}

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        file_bytes = Mock()
        metadata = {"filename": "test.txt"}
        
        json_response, http_status = await self.api.submit(file_bytes, metadata, "test-api-key", "192.168.1.1")

        self.assertEqual(http_status, 200)
        self.assertEqual(json_response["data_id"], "test-data-id")
        self.assertEqual(json_response["status"], "submitted")
        mock_client.post.assert_called_once()

        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        
        json_response, http_status = await self.api.submit(file_bytes, metadata, "test-api-key")

        self.assertEqual(http_status, 500)
        self.assertIn("error", json_response)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_result_success(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "data_id": "test-data-id",
            "process_info": {"progress_percentage": 100}
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        json_response, http_status = await self.api.check_result("test-data-id", "test-api-key", "192.168.1.1")

        self.assertEqual(http_status, 200)
        self.assertEqual(json_response["data_id"], "test-data-id")
        mock_client.get.assert_called_once()

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_check_hash_scenarios(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {
            "hash": "abc123",
            "status": "found"
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        json_response, http_status = await self.api.check_hash("abc123", "test-api-key", "192.168.1.1")

        self.assertEqual(http_status, 200)
        self.assertEqual(json_response["sha256"], "abc123")
        mock_client.get.assert_called_once()

        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "not found"}

        json_response, http_status = await self.api.check_hash("unknown-hash", "test-api-key", "192.168.1.1")

        self.assertEqual(http_status, 404)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_get_sanitized_file_headers_scenarios(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.headers = {
            'Content-Type': 'application/octet-stream',
            'Content-Length': '1024',
            'Content-Disposition': 'attachment; filename="test.txt"'
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        headers = await self.api.get_sanitized_file_headers("test-data-id", "test-api-key")

        self.assertIn('Content-Type', headers)
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        mock_client.get.assert_called_once()

        mock_client.get = AsyncMock(side_effect=Exception("Network error"))

        headers = await self.api.get_sanitized_file_headers("test-data-id", "test-api-key")

        self.assertEqual(headers, {})

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_request_as_json_scenarios(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {"message": "success"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        json_response, status = await self.api._request_as_json("check_result", fields={"data_id": "test-id"})

        self.assertEqual(status, 200)
        self.assertEqual(json_response["message"], "success")

        mock_response2 = MagicMock()
        mock_response2.status_code = 201
        mock_response2.headers.get.return_value = 'application/json'
        mock_response2.json.return_value = {"created": True}
        mock_client.post = AsyncMock(return_value=mock_response2)

        json_response, status = await self.api._request_as_json("file_submit", data={"test": "data"})

        self.assertEqual(status, 201)
        self.assertTrue(json_response["created"])

        mock_response3 = MagicMock()
        mock_response3.status_code = 200
        mock_response3.headers.get.return_value = 'text/plain'
        mock_response3.text = AsyncMock(return_value="Plain text response")
        mock_client.get = AsyncMock(return_value=mock_response3)

        text_response, status = await self.api._request_as_json("check_result", fields={"data_id": "test-id"})

        self.assertEqual(status, 200)
        self.assertEqual(text_response, "Plain text response")

    def test_get_url_scenarios(self):
        url = self.api._get_url("file_submit")
        self.assertEqual(url, "https://mock-url.com/file")

        url = self.api._get_url("check_result", {"data_id": "test-id-123"})
        self.assertEqual(url, "https://mock-url.com/file/test-id-123")

        url = self.api._get_url("sanitized_file", {"data_id": "sanitized-id"})
        self.assertEqual(url, "https://mock-url.com/file/converted/sanitized-id")

    def test_get_decoded_parameter_scenarios(self):
        result = self.api._get_decoded_parameter(None)
        self.assertIsNone(result)

        result = self.api._get_decoded_parameter("test.txt")
        self.assertEqual(result, "test.txt")

        param = str([b"test.txt"])
        result = self.api._get_decoded_parameter(param)
        self.assertEqual(result, "test.txt")

        result = self.api._get_decoded_parameter("[invalid")
        self.assertEqual(result, "[invalid")

    def test_add_scan_with_header_scenarios(self):
        headers = {'apikey': 'test'}
        result = self.api._add_scan_with_header(headers)
        self.assertNotIn('scanWith', result)
        self.assertEqual(result, headers)

        self.api.service_name = SERVICE.meta_defender_cloud
        headers = {'apikey': 'test'}
        result = self.api._add_scan_with_header(headers)
        self.assertNotIn('scanWith', result)

        self.api.settings['headers_scan_with'] = 'custom-scanner'
        headers = {'apikey': 'test'}
        result = self.api._add_scan_with_header(headers)
        self.assertEqual(result['scanWith'], 'custom-scanner')

        self.api.settings['headers_scan_with'] = '   '
        headers = {'apikey': 'test'}
        result = self.api._add_scan_with_header(headers)
        self.assertNotIn('scanWith', result)

    def test_check_analysis_complete_scenarios(self):
        json_response = {
            "process_info": {
                "progress_percentage": 100
            }
        }
        result = self.api.check_analysis_complete(json_response)
        self.assertTrue(result)

        json_response = {
            "process_info": {
                "progress_percentage": 50
            }
        }
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)

        json_response = {"status": "processing"}
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)

    def test_get_sanitized_file_path_scenarios(self):
        json_response = {
            "data_id": "test-id",
            "process_info": {
                "post_processing": {
                    "actions_ran": ["Sanitized", "OtherAction"]
                }
            }
        }
        result = self.api.get_sanitized_file_path(json_response)
        self.assertEqual(result, "https://mock-url.com/file/converted/test-id")

        json_response = {
            "data_id": "test-id",
            "process_info": {
                "post_processing": {
                    "actions_ran": ["OtherAction"]
                }
            }
        }
        result = self.api.get_sanitized_file_path(json_response)
        self.assertEqual(result, '')

        json_response = {"data_id": "test-id"}
        result = self.api.get_sanitized_file_path(json_response)
        self.assertEqual(result, '')

    def test_get_submit_file_headers_scenarios(self):
        metadata = {"filename": "test.txt"}
        headers = self.api._get_submit_file_headers(metadata, "test-api-key", "192.168.1.1")
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['apikey'], 'test-api-key')
        self.assertEqual(headers['x-forwarded-for'], '192.168.1.1')
        self.assertEqual(headers['x-real-ip'], '192.168.1.1')

        headers = self.api._get_submit_file_headers(metadata, "test-api-key", None)
        
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['apikey'], 'test-api-key')
        self.assertNotIn('x-forwarded-for', headers)
        self.assertNotIn('x-real-ip', headers)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_sanitized_file_success(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {"file": "data"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        json_response, status = await self.api.sanitized_file("test-data-id", "test-api-key", "192.168.1.1")

        self.assertEqual(status, 200)
        self.assertEqual(json_response["file"], "data")

    async def test_config_and_get_instance(self):
        MetaDefenderAPI.config(self.settings, "https://test-url.com", "test-api-key", MetaDefenderAPIImpl)
        instance = MetaDefenderAPI.get_instance()

        self.assertIsInstance(instance, MetaDefenderAPIImpl)
        self.assertEqual(instance.server_url, "https://test-url.com")
        self.assertEqual(instance.apikey, "test-api-key")

    def test_singleton_instance(self):
        MetaDefenderAPI._instance = None
        MetaDefenderAPI.config(self.settings, "https://singleton-test.com", "singleton-key", MetaDefenderAPIImpl)
        
        instance1 = MetaDefenderAPI.get_instance()
        instance2 = MetaDefenderAPI.get_instance()
        
        self.assertIs(instance1, instance2)

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_request_as_json_status(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers.get.return_value = 'application/json'
        mock_response.json.return_value = {"result": "success"}

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client

        json_response, status = await self.api._request_as_json_status("check_result", fields={"data_id": "test-id"})

        self.assertEqual(status, 200)
        self.assertEqual(json_response["result"], "success")

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_request_as_bytes_success(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read = AsyncMock(return_value=b"test file content")
        
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        content, status = await self.api._request_as_bytes("hash_lookup", fields={"hash": "test-hash"})
        
        self.assertEqual(status, 200)
        self.assertEqual(content, b"test file content")
        mock_client.get.assert_called_once()

    @patch('metadefender_menlo.api.utils.http_client_manager.HttpClientManager.get_client')
    async def test_request_status_scenarios(self, mock_get_client):
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.read = MagicMock(return_value=b"post response content")
        
        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_get_client.return_value = mock_client
        
        content, status = await self.api._request_status("file_submit", data={"test": "data"})
        
        self.assertEqual(status, 201)
        self.assertEqual(content, b"post response content")
        mock_client.post.assert_called_once()

        mock_response.status_code = 200
        mock_response.read = MagicMock(return_value=b"get response content")
        mock_client.get = AsyncMock(return_value=mock_response)
        
        content, status = await self.api._request_status("check_result", fields={"data_id": "test-id"})
        
        self.assertEqual(status, 200)
        self.assertEqual(content, b"get response content")
        mock_client.get.assert_called_once()

    def test_add_scan_with_header_exception_handling(self):
        cloud_settings = self.settings.copy()
        cloud_settings['headers_scan_with'] = 'test-value'
        
        cloud_api = MetaDefenderAPIImpl(cloud_settings, "https://cloud-url.com", "cloud-key")
        cloud_api.service_name = SERVICE.meta_defender_cloud
        
        with patch.object(cloud_api, 'settings', side_effect=Exception("Mocked settings error")):
            headers = {'apikey': 'test-key'}
            result = cloud_api._add_scan_with_header(headers)
            self.assertEqual(result, headers)
            self.assertNotIn('scanWith', result)

    def test_add_scan_with_header_settings_edge_cases(self):
        cloud_api = MetaDefenderAPIImpl(self.settings, "https://cloud-url.com", "cloud-key")
        cloud_api.service_name = SERVICE.meta_defender_cloud
        
        delattr(cloud_api, 'settings')
        headers = {'apikey': 'test-key'}
        result = cloud_api._add_scan_with_header(headers)
        self.assertEqual(result, headers)
        self.assertNotIn('scanWith', result)

        cloud_api.settings = None
        result = cloud_api._add_scan_with_header(headers)
        self.assertEqual(result, headers)
        self.assertNotIn('scanWith', result)

if __name__ == '__main__':
    unittest.main()
