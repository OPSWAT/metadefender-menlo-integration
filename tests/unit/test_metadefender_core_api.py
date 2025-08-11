import unittest
from unittest.mock import patch

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI

class TestMetaDefenderCoreAPI(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'headers_engines_metadata': 'some_metadata',
            'fallbackToOriginal': True,
            'scanWith': 'mdaas'
        }
        self.url = "https://test-server.com"
        self.apikey = "test_api_key"
        self.api = MetaDefenderCoreAPI(self.settings, self.url, self.apikey)

    def test_get_submit_file_headers(self):
        filename = "test_file.txt"
        metadata = {"key": "value"}
        
        headers = self.api._get_submit_file_headers(filename, metadata)

        expected_headers = {
            "Content-Type": "application/octet-stream",
            "filename": "test_file.txt",
            "metadata": '{"key": "value"}',
            "engines-metadata": self.settings['headers_engines_metadata'],
            "scanWith": "mdaas"
        }
        self.assertEqual(headers, expected_headers)

    def test_check_analysis_complete_success(self):
        json_response = {"process_info": {"progress_percentage": 100}}
        self.assertTrue(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_incomplete(self):
        json_response = {"process_info": {"progress_percentage": 50}}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_unexpected_response(self):
        json_response = {}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.MetaDefenderCoreAPI._request_status')
    async def test_retrieve_sanitized_file_success(self, mock_request_status):
        mock_request_status.return_value = ({"file_content": "sanitized file content"}, 200)

        response, http_status = await self.api.retrieve_sanitized_file("test_data_id", self.apikey, "0.0.0.0")

        self.assertEqual(http_status, 200)
        self.assertEqual(response, {"file_content": "sanitized file content"})

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.MetaDefenderCoreAPI._request_status')
    async def test_retrieve_sanitized_file_not_found_fallback(self, mock_request_status):
        mock_request_status.return_value = (None, 404)

        response, http_status = await self.api.retrieve_sanitized_file("test_data_id", self.apikey, "0.0.0.0")

        self.assertEqual(http_status, 204)
        self.assertEqual(response, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_core_api.MetaDefenderCoreAPI._request_status')
    async def test_retrieve_sanitized_file_not_found_no_fallback(self, mock_request_status):
        self.api.settings['fallbackToOriginal'] = False
        mock_request_status.return_value = (None, 404)

        response, http_status = await self.api.retrieve_sanitized_file("test_data_id", self.apikey, "0.0.0.0")

        self.assertEqual(http_status, 404)
        self.assertIsNone(response)

if __name__ == '__main__':
    unittest.main()
