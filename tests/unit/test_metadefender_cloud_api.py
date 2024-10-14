import unittest
from unittest.mock import patch, Mock, AsyncMock
import urllib.parse

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

class TestMetaDefenderCloudAPI(unittest.TestCase):
    
    def setUp(self):
        self.settings = {'scanRule': 'test_rule'}
        self.url = 'https://test.url'
        self.apikey = 'test_apikey'
        self.api = MetaDefenderCloudAPI(self.settings, self.url, self.apikey)

    def test_init(self):
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(self.api.report_url, "https://metadefender.opswat.com/results/file/{data_id}/regular/overview")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.debug')
    def test_get_submit_file_headers(self, mock_debug):
        filename = "test_file.txt"
        metadata = {}
        headers = self.api._get_submit_file_headers(filename, metadata)

        expected_headers = {
            "filename": "test_file.txt",
            "Content-Type": "application/octet-stream",
            "rule": self.settings['scanRule']
        }
        self.assertEqual(headers, expected_headers)
        mock_debug.assert_called_once()

    def test_check_analysis_complete_true(self):
        json_response = {'sanitized': {'progress_percentage': 100}}
        self.assertTrue(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_false(self):
        json_response = {'sanitized': {'progress_percentage': 50}}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_missing_info(self):
        json_response = {'other_info': 'some_data'}
        with patch('builtins.print') as mock_print:
            self.assertFalse(self.api.check_analysis_complete(json_response))
            mock_print.assert_called_once_with("Unexpected response from MetaDefender: {'other_info': 'some_data'}")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._download_sanitized_file')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    async def test_retrieve_sanitized_file_success(self, mock_logging, mock_download, mock_request):
        mock_request.return_value = ({"sanitizedFilePath": "https://test.file"}, 200)
        mock_download.return_value = (b"file_content", 200)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')

        self.assertEqual(status, 200)
        self.assertEqual(response, b"file_content")
        mock_logging.assert_called()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    async def test_retrieve_sanitized_file_unauthorized(self, mock_logging, mock_request):
        mock_request.return_value = ({"error": "Unauthorized"}, 401)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')

        self.assertEqual(status, 401)
        self.assertEqual(response, {"error": "Unauthorized"})
        mock_logging.assert_called()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.info')
    async def test_retrieve_sanitized_file_not_available(self, mock_logging, mock_request):
        mock_request.return_value = ({"sanitizedFilePath": ""}, 200)

        response, status = await self.api.retrieve_sanitized_file('test_id', 'test_apikey', 'test_ip')

        self.assertEqual(status, 204)
        self.assertEqual(response, "")
        mock_logging.assert_called()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_error')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_download_sanitized_file_error(self, mock_client, mock_handle_error):
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download error")
        mock_handle_error.return_value = ({"error": "Download error"}, 500)

        response, status = await self.api._download_sanitized_file('https://test.file', 'test_apikey')

        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "Download error"})
        mock_handle_error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._parse_sanitized_data')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._get_failure_reasons')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._log_sanitization_result')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_handle_no_sanitized_file(self, mock_client, mock_log_result, mock_get_failure_reasons, mock_parse_data):
        mock_response = Mock()
        mock_response.content = json.dumps({"sanitized": {}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        mock_parse_data.return_value = {}
        mock_get_failure_reasons.return_value = ""
        mock_log_result.return_value = ("", 204)

        response, status = await self.api._handle_no_sanitized_file('test_id', 'test_apikey')

        self.assertEqual(status, 204)
        self.assertEqual(response, "")
        mock_log_result.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging.error')
    def test_handle_error(self, mock_logging):
        error = Exception("An error occurred")
        response, status = self.api._handle_error(error, 'test_apikey')

        self.assertEqual(status, 500)
        self.assertEqual(response, {"error": "An error occurred"})
        mock_logging.assert_called_once_with(
            "{0} > {1} > {2}".format(
                SERVICE.MenloPlugin, TYPE.Internal, repr(error)
            ), {'apikey': 'test_apikey'}
        )


if __name__ == '__main__':
    unittest.main()