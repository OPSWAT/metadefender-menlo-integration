import unittest
from unittest.mock import patch, AsyncMock, MagicMock
import json
from tornado.httpclient import HTTPClientError

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI  

class MetaDefenderAPIImpl(MetaDefenderAPI):
    def __init__(self, url, apikey):
        super().__init__(url, apikey)

    def _get_submit_file_headers(self, filename, metadata):
        return {'Content-Type': 'application/octet-stream'}

    def check_analysis_complete(self, json_response):
        return json_response.get("status") == "completed"

    async def retrieve_sanitized_file(self, data_id, apikey, ip):
        return await self._request_as_json_status("sanitized_file", fields={"data_id": data_id},
                                                  headers={'apikey': apikey, 'x-forwarded-for': ip, 'x-real-ip': ip})


class MetaDefenderAPITest(unittest.TestCase):
    def setUp(self):
        self.api = MetaDefenderAPIImpl("https://mock-url", "mock-api-key")

    @patch('httpx.AsyncClient')
    async def test_submit_file_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"status": "submitted"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        filename = "test_file.txt"
        fp = b"mock file content"
        metadata = {"key": "value"}
        json_response, http_status = await self.api.submit_file(filename, fp, metadata)

        self.assertEqual(http_status, 200)
        self.assertEqual(json.loads(json_response), {"status": "submitted"})

    @patch('httpx.AsyncClient')
    async def test_submit_file_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.content = json.dumps({"error": "Internal Server Error"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        filename = "test_file.txt"
        fp = b"mock file content"
        metadata = {"key": "value"}
        json_response, http_status = await self.api.submit_file(filename, fp, metadata)

        self.assertEqual(http_status, 500)
        self.assertIn("error", json.loads(json_response))

    @patch('httpx.AsyncClient')
    async def test_retrieve_result_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"status": "completed"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        data_id = "mock_data_id"
        json_response, http_status = await self.api.retrieve_result(data_id, "mock-api-key")

        self.assertEqual(http_status, 200)
        self.assertEqual(json.loads(json_response), {"status": "completed"})

    @patch('httpx.AsyncClient')
    async def test_retrieve_result_incomplete_analysis(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"status": "in_progress"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        data_id = "mock_data_id"

        with self.assertRaises(Exception):
            await self.api.retrieve_result(data_id, "mock-api-key")

    @patch('httpx.AsyncClient')
    async def test_hash_lookup_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"hash": "mock_hash", "status": "found"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        sha256 = "mock_sha256"
        json_response, http_status = await self.api.hash_lookup(sha256, "mock-api-key", "192.0.2.1")

        self.assertEqual(http_status, 200)
        self.assertEqual(json.loads(json_response), {"hash": "mock_hash", "status": "found"})

    @patch('httpx.AsyncClient')
    async def test_hash_lookup_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.content = json.dumps({"error": "not found"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        sha256 = "mock_sha256"
        json_response, http_status = await self.api.hash_lookup(sha256, "mock-api-key", "192.0.2.1")

        self.assertEqual(http_status, 404)
        self.assertIn("error", json.loads(json_response))

    @patch('httpx.AsyncClient')
    async def test_check_result_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"analysis_completed": True}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        data_id = "mock_data_id"
        json_response, http_status = await self.api.check_result(data_id, "mock-api-key", "192.0.2.1")

        self.assertEqual(http_status, 200)
        self.assertTrue(json.loads(json_response)["analysis_completed"])

    @patch('httpx.AsyncClient')
    async def test_request_as_json_status_success(self, mock_client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = json.dumps({"message": "success"}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(return_value=mock_response)

        json_response, http_status = await self.api._request_as_json_status("submit_file")

        self.assertEqual(http_status, 200)
        self.assertEqual(json.loads(json_response), {"message": "success"})

    @patch('httpx.AsyncClient')
    async def test_request_as_json_status_error(self, mock_client):
        mock_client.return_value.__aenter__.return_value.request = AsyncMock(side_effect=HTTPClientError)

        with self.assertRaises(HTTPClientError):
            await self.api._request_as_json_status("submit_file")

    async def test_config_and_get_instance(self):
        MetaDefenderAPI.config("settings", "https://mock-url", "mock-api-key", MetaDefenderAPIImpl)
        instance = MetaDefenderAPI.get_instance()

        self.assertIsInstance(instance, MetaDefenderAPIImpl)
        self.assertEqual(instance.server_url, "https://mock-url")
        self.assertEqual(instance.apikey, "mock-api-key")


if __name__ == '__main__':
    unittest.main()
