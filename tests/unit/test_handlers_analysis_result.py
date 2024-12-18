import unittest
from unittest.mock import Mock, patch, AsyncMock

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.analysis_result import AnalysisResultHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class TestAnalysisResultHandler(unittest.TestCase):
    def setUp(self):
        self.application = Mock()
        self.application.ui_methods = {}
        self.application.ui_modules = {}
        self.request = Mock()

        self.handler = AnalysisResultHandler(
            application=self.application,
            request=self.request
        )

        self.handler.metaDefenderAPI = Mock()
        self.handler.client_ip = '127.0.0.1'
        self.handler.json_response = Mock()

        self.original_logging_info = logging.info
        self.original_logging_error = logging.error

        logging.info = Mock()
        logging.error = Mock()

    def tearDown(self):
        logging.info = self.original_logging_info
        logging.error = self.original_logging_error

    @patch('metadefender_menlo.api.responses.file_analysis.FileAnalyis')
    async def test_get_success(self, mock_file_analysis):
        # Arrange
        test_uuid = 'test_uuid'
        test_apikey = 'test_apikey'
        test_response = {'result': 'clean'}
        test_status = 200

        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}

        self.handler.metaDefenderAPI.check_result = AsyncMock(
            return_value=(test_response, test_status)
        )

        mock_file_analysis_instance = mock_file_analysis.return_value
        mock_file_analysis_instance.handle_response.return_value = (
            test_response,
            test_status
        )

        await self.handler.get()

        self.handler.get_argument.assert_called_once_with('uuid')
        logging.info.assert_called_once_with(
            "MenloPlugin > Request > {'method': 'GET', 'endpoint': '/api/v1/result/test_uuid'}"
        )
        self.handler.metaDefenderAPI.check_result.assert_called_once_with(
            test_uuid,
            test_apikey,
            self.handler.client_ip
        )
        mock_file_analysis_instance.handle_response.assert_called_once_with(
            test_status,
            test_response
        )
        self.handler.json_response.assert_called_once_with(
            test_response,
            test_status
        )

    async def test_get_missing_uuid(self):
        self.handler.get_argument = Mock(side_effect=Exception("Missing argument uuid"))

        await self.handler.get()

        self.handler.get_argument.assert_called_once_with('uuid')
        self.handler.json_response.assert_called_once_with({}, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.responses.file_analysis.FileAnalyis')
    async def test_get_api_error(self, mock_file_analysis):
        test_uuid = 'test_uuid'
        test_apikey = 'test_apikey'

        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.check_result = AsyncMock(
            side_effect=Exception("API Error")
        )

        await self.handler.get()

        self.handler.json_response.assert_called_once_with({}, 500)
        logging.error.assert_called_once()

    @patch('metadefender_menlo.api.responses.file_analysis.FileAnalyis')
    async def test_get_file_analysis_error(self, mock_file_analysis):
        test_uuid = 'test_uuid'
        test_apikey = 'test_apikey'
        test_response = {'result': 'clean'}
        test_status = 200

        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {'Authorization': test_apikey}
        self.handler.metaDefenderAPI.check_result = AsyncMock(
            return_value=(test_response, test_status)
        )

        mock_file_analysis_instance = mock_file_analysis.return_value
        mock_file_analysis_instance.handle_response.side_effect = Exception("Processing Error")

        await self.handler.get()

        self.handler.json_response.assert_called_once_with({}, 500)
        logging.error.assert_called_once_with(
            "{0} > {1} > {2}".format(
                SERVICE.MetaDefenderCloud,
                TYPE.Response,
                {"error": "Exception('Processing Error')"}
            ),
            {'apikey': test_apikey}
        )

    async def test_get_missing_auth_header(self):
        test_uuid = 'test_uuid'
        test_response = {'error': 'unauthorized'}
        test_status = 401

        self.handler.get_argument = Mock(return_value=test_uuid)
        self.handler.request.headers = {}  

        self.handler.metaDefenderAPI.check_result = AsyncMock(
            return_value=(test_response, test_status)
        )

        await self.handler.get()

        self.handler.metaDefenderAPI.check_result.assert_called_once_with(
            test_uuid,
            None,
            self.handler.client_ip
        )
        logging.info.assert_called_once_with(
            "MenloPlugin > Request > {'method': 'GET', 'endpoint': '/api/v1/result/test_uuid'}"
        )


if __name__ == '__main__':
    unittest.main()