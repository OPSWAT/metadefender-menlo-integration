import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import json
import httpx
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI

class TestMetaDefenderCloudAPI(unittest.TestCase):
    def setUp(self):
        self.settings = {'scanRule': 'test_rule'}
        self.url = 'https://api.metadefender.com'
        self.apikey = 'test_apikey'
        self.api = MetaDefenderCloudAPI(self.settings, self.url, self.apikey)

    def test_init(self):
        self.assertEqual(self.api.settings, self.settings)
        self.assertEqual(self.api.server_url, self.url)
        self.assertEqual(self.api.apikey, self.apikey)
        self.assertEqual(self.api.report_url, "https://metadefender.opswat.com/results/file/{data_id}/regular/overview")

    def test_get_submit_file_headers(self):
        filename = 'test_file.txt'
        metadata = {}
        headers = self.api._get_submit_file_headers(filename, metadata)
        self.assertEqual(headers['filename'], 'test_file.txt')
        self.assertEqual(headers['Content-Type'], 'application/octet-stream')
        self.assertEqual(headers['rule'], 'test_rule')

    def test_check_analysis_complete_true(self):
        json_response = {'sanitized': {'progress_percentage': 100}}
        self.assertTrue(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_false(self):
        json_response = {'sanitized': {'progress_percentage': 50}}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    def test_check_analysis_complete_unexpected(self):
        json_response = {'unexpected': 'response'}
        self.assertFalse(self.api.check_analysis_complete(json_response))

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_response(self, mock_logging):
        response = {'key': 'value'}
        http_status = 200
        self.api._log_response(response, http_status)
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_unauthorized(self, mock_logging):
        response = {'error': 'Unauthorized'}
        http_status = 401
        result = self.api._handle_unauthorized(response, http_status)
        mock_logging.info.assert_called_once()
        self.assertEqual(result, (response, http_status))

    @patch('httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_download_sanitized_file_success(self, mock_logging, mock_client):
        mock_response = MagicMock()
        mock_response.content = b'file_content'
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        fileurl = 'https://example.com/file'
        result = await self.api._download_sanitized_file(fileurl, self.apikey)

        self.assertEqual(result, (b'file_content', 200))
        mock_logging.info.assert_called_once()

    @patch('httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_download_sanitized_file_error(self, mock_logging, mock_client):
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception('Download failed')

        fileurl = 'https://example.com/file'
        result = await self.api._download_sanitized_file(fileurl, self.apikey)

        self.assertEqual(result, ({"error": "Download failed"}, 500))
        mock_logging.error.assert_called_once()

    @patch('httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_handle_no_sanitized_file_with_failure_reasons(self, mock_logging, mock_client):
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "sanitized": {"failure_reasons": ["reason1", "reason2"]}
        }).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ("", 204))
        mock_logging.info.assert_called_with(
            "{0} > {1} > {2}".format("MenloPlugin", "Response", {
                "message": "Sanitization failed with failure reasons.",
                "failure_reasons": ["reason1", "reason2"],
                "status": 204
            })
        )

    @patch('httpx.AsyncClient')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_handle_no_sanitized_file_without_failure_reasons(self, mock_logging, mock_client):
        mock_response = MagicMock()
        mock_response.content = json.dumps({"sanitized": {}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ("", 204))
        mock_logging.info.assert_called_with(
            "{0} > {1} > {2}".format("MenloPlugin", "Response", {
                "message": "Sanitized file not available!", "status": 204
            })
        )

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_handle_error(self, mock_logging):
        error = Exception("Test error")
        result = self.api._handle_error(error, self.apikey)

        self.assertEqual(result, ({"error": "Test error"}, 500))
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._download_sanitized_file')
    async def test_retrieve_sanitized_file_success(self, mock_download, mock_request):
        mock_request.return_value = ({"sanitizedFilePath": "https://example.com/file"}, 200)
        mock_download.return_value = (b'file_content', 200)

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, (b'file_content', 200))
        mock_request.assert_called_once()
        mock_download.assert_called_once_with("https://example.com/file", self.apikey)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_unauthorized')
    async def test_retrieve_sanitized_file_unauthorized(self, mock_unauthorized, mock_request):
        mock_request.return_value = ({"error": "Unauthorized"}, 401)
        mock_unauthorized.return_value = ({"error": "Unauthorized"}, 401)

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ({"error": "Unauthorized"}, 401))
        mock_request.assert_called_once()
        mock_unauthorized.assert_called_once_with({"error": "Unauthorized"}, 401)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._request_as_json_status')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.MetaDefenderCloudAPI._handle_no_sanitized_file')
    async def test_retrieve_sanitized_file_no_file(self, mock_no_file, mock_request):
        mock_request.return_value = ({"sanitizedFilePath": ""}, 200)
        mock_no_file.return_value = ("", 204)

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ("", 204))
        mock_request.assert_called_once()
        mock_no_file.assert_called_once_with('data_id', self.apikey)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_retrieve_sanitized_file_no_file_path(self, mock_logging):
        self.api._request_as_json_status = AsyncMock(return_value=({"sanitizedFilePath": ""}, 200))
        self.api._handle_no_sanitized_file = AsyncMock(return_value=("", 204))

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ("", 204))
        self.api._handle_no_sanitized_file.assert_called_once_with('data_id', self.apikey)

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_exception(self, mock_client):
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Test error")

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ({"error": "Test error"}, 500))

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_with_reason(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = json.dumps({"sanitized": {"reason": "Test reason"}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ("", 204))

    def test_parse_sanitized_data(self):
        mock_response = MagicMock()
        mock_response.content = json.dumps({"sanitized": {"test": "data"}}).encode('utf-8')
        result = self.api._parse_sanitized_data(mock_response)
        self.assertEqual(result, {"test": "data"})

    def test_get_failure_reasons_with_failure_reasons(self):
        sanitized_data = {"failure_reasons": ["reason1", "reason2"]}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, ["reason1", "reason2"])

    def test_get_failure_reasons_with_reason(self):
        sanitized_data = {"reason": "Test reason"}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, "Test reason")

    def test_get_failure_reasons_empty(self):
        sanitized_data = {}
        result = self.api._get_failure_reasons(sanitized_data)
        self.assertEqual(result, "")

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_with_failure_reasons(self, mock_logging):
        failure_reasons = ["reason1", "reason2"]
        result = self.api._log_sanitization_result(failure_reasons)
        self.assertEqual(result, ("", 204))
        mock_logging.info.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_log_sanitization_result_without_failure_reasons(self, mock_logging):
        failure_reasons = []
        result = self.api._log_sanitization_result(failure_reasons)
        self.assertEqual(result, ("", 204))
        mock_logging.info.assert_called_once()

    def test_check_analysis_complete_missing_sanitized(self):
        json_response = {'some_key': 'some_value'}
        result = self.api.check_analysis_complete(json_response)
        self.assertFalse(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.httpx.AsyncClient')
    async def test_retrieve_sanitized_file_download_error(self, mock_client, mock_logging):
        mock_response = MagicMock()
        mock_response.json.return_value = {"sanitizedFilePath": "https://example.com/file"}
        self.api._request_as_json_status = AsyncMock(return_value=(mock_response.json(), 200))
        
        mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Download failed")

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ({"error": "Download failed"}, 500))
        mock_logging.error.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_retrieve_sanitized_file_request_error(self, mock_logging):
        self.api._request_as_json_status = AsyncMock(side_effect=Exception("Request failed"))

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ({"error": "Request failed"}, 500))
        mock_logging.error.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_download_sanitized_file_client_error(self, mock_client):
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection error")

        result = await self.api._download_sanitized_file("https://example.com/file", self.apikey)

        self.assertEqual(result, ({"error": "Connection error"}, 500))

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_client_error(self, mock_client):
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.RequestError("Connection error")

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ({"error": "Connection error"}, 500))

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_invalid_json(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = b'Invalid JSON'
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ({"error": "Invalid JSON response"}, 500))
    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    def test_get_submit_file_headers_with_special_characters(self, mock_logging):
        filename = 'test file with spaces.txt'
        metadata = {}
        headers = self.api._get_submit_file_headers(filename, metadata)
        self.assertEqual(headers['filename'], 'test%20file%20with%20spaces.txt')
        mock_logging.debug.assert_called_once()

    @patch('metadefender_menlo.api.metadefender.metadefender_cloud_api.logging')
    async def test_retrieve_sanitized_file_no_file_path_error(self, mock_logging):
        self.api._request_as_json_status = AsyncMock(return_value=({"error": "No file path"}, 400))
        self.api._handle_unauthorized = MagicMock(return_value=({"error": "Unauthorized"}, 401))

        result = await self.api.retrieve_sanitized_file('data_id', self.apikey, '127.0.0.1')

        self.assertEqual(result, ({"error": "Unauthorized"}, 401))
        self.api._handle_unauthorized.assert_called_once_with({"error": "No file path"}, 400)

    @patch('httpx.AsyncClient')
    async def test_download_sanitized_file_http_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTP Error", request=MagicMock(), response=MagicMock())
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._download_sanitized_file("https://example.com/file", self.apikey)

        self.assertEqual(result[1], 500)  # Check if the status code is 500
        self.assertIn("error", result[0])  # Check if the response contains an error message

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_http_error(self, mock_client):
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("HTTP Error", request=MagicMock(), response=MagicMock())
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result[1], 500)  # Check if the status code is 500
        self.assertIn("error", result[0])  # Check if the response contains an error message

    @patch('httpx.AsyncClient')
    async def test_handle_no_sanitized_file_no_sanitized_key(self, mock_client):
        mock_response = MagicMock()
        mock_response.content = json.dumps({"no_sanitized_key": {}}).encode('utf-8')
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

        result = await self.api._handle_no_sanitized_file('data_id', self.apikey)

        self.assertEqual(result, ("", 204))

if __name__ == '__main__':
    unittest.main()
