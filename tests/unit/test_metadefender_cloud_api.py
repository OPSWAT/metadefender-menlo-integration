import unittest
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI

@pytest.fixture
def api():
    settings = {'scanRule': 'test_rule'}
    return MetaDefenderCloudAPI(settings, 'https://api.metadefender.com', 'test_apikey')

def test_init(api):
    assert api.settings == {'scanRule': 'test_rule'}
    assert api.server_url == 'https://api.metadefender.com'
    assert api.apikey == 'test_apikey'
    assert api.report_url == "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"

def test_get_submit_file_headers(api):
    filename = 'test_file.txt'
    metadata = {}
    headers = api._get_submit_file_headers(filename, metadata)
    assert headers['filename'] == 'test_file.txt'
    assert headers['Content-Type'] == 'application/octet-stream'
    assert headers['rule'] == 'test_rule'

@pytest.mark.parametrize("json_response, expected", [
    ({"sanitized": {"progress_percentage": 100}}, True),
    ({"sanitized": {"progress_percentage": 50}}, False),
    ({}, False),
])
def test_check_analysis_complete(api, json_response, expected):
    assert api.check_analysis_complete(json_response) == expected

@patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI._request_as_json_status')
@patch('httpx.AsyncClient.get')
def test_retrieve_sanitized_file_success(mock_get, mock_request, api):
    mock_response = MagicMock()
    mock_response.content = b"sanitized content"
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    mock_request.return_value = ({"sanitizedFilePath": "http://example.com/file"}, 200)

    result, status = api.retrieve_sanitized_file('test_data_id', 'test_apikey', '127.0.0.1')

    assert result == b"sanitized content"
    assert status == 200

@patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI._request_as_json_status')
def test_retrieve_sanitized_file_unauthorized(mock_request, api):
    mock_request.return_value = ({"error": "Unauthorized"}, 401)

    result, status = api.retrieve_sanitized_file('test_data_id', 'test_apikey', '127.0.0.1')

    assert result == {"error": "Unauthorized"}
    assert status == 401

@patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI._request_as_json_status')
@patch('httpx.AsyncClient.get')
def test_retrieve_sanitized_file_no_url(mock_get, mock_request, api):
    mock_response = MagicMock()
    mock_response.content = json.dumps({"sanitized": {"failure_reasons": "Test failure"}}).encode()
    mock_response.status_code = 200
    mock_get.return_value = mock_response
    mock_request.return_value = ({}, 200)

    result, status = api.retrieve_sanitized_file('test_data_id', 'test_apikey', '127.0.0.1')

    assert result == ""
    assert status == 204

@patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI._request_as_json_status')
def test_retrieve_sanitized_file_exception(mock_request, api):
    mock_request.side_effect = Exception("Test exception")

    result, status = api.retrieve_sanitized_file('test_data_id', 'test_apikey', '127.0.0.1')

    assert result == {}
    assert status == 500

@patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI._request_as_json_status')
@patch('httpx.AsyncClient.get')
def test_retrieve_sanitized_file_download_exception(mock_get, mock_request, api):
    mock_request.return_value = ({"sanitizedFilePath": "http://example.com/file"}, 200)
    mock_get.side_effect = Exception("Download error")

    result, status = api.retrieve_sanitized_file('test_data_id', 'test_apikey', '127.0.0.1')

    assert result == {"error": "Download error"}
    assert status == 500


if __name__ == '__main__':
    unittest.main()
