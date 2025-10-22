import unittest
from unittest.mock import patch, Mock
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.submit_response import SubmitResponse
from metadefender_menlo.api.responses.base_response import BaseResponse

class TestFileSubmit(unittest.TestCase):

    def setUp(self):
        self.file_submit = SubmitResponse()

    def test_init(self):
        self.assertIsInstance(self.file_submit, BaseResponse)
        self.assertEqual(self.file_submit._allowed_responses, [200, 400, 401, 411, 422, 429, 500, 503])
        for code in ["200", "400", "401", "411", "422", "429"]:
            self.assertIn(code, self.file_submit._http_responses)

    def test_response200_scenarios(self):
        test_cases = [
            ({"data_id": "test_id"}, {"uuid": "test_id", "result": "accepted"}, 200),
            ({}, {"result": "skip"}, 200)
        ]
        
        for json_response, expected_result, expected_status in test_cases:
            with self.subTest(json_response=json_response):
                result, status_code = asyncio.run(self.file_submit._SubmitResponse__response200(json_response, 200))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    @patch.object(BaseResponse, '_translate')
    def test_response200_translate_calls(self, mock_translate):
        json_response = {"data_id": "test_id"}
        asyncio.run(self.file_submit._SubmitResponse__response200(json_response, 200))
        
        expected_calls = [
            ('uuid', {'uuid': '{0}', 'result': '{0}'}, 'test_id'),
            ('result', {'uuid': '{0}', 'result': '{0}'}, 'accepted')
        ]
        for call_args in expected_calls:
            mock_translate.assert_any_call(*call_args)
        
        mock_translate.reset_mock()
        
        json_response = {}
        asyncio.run(self.file_submit._SubmitResponse__response200(json_response, 200))
        
        mock_translate.assert_called_once_with('result', {'result': '{0}'}, 'skip')

    @patch('logging.error')
    @patch.object(BaseResponse, '_translate')
    def test_response200_exception_handling(self, mock_translate, mock_logging):
        mock_translate.side_effect = Exception("Test error")
        json_response = {"data_id": "test_id"}
        
        result, status_code = asyncio.run(self.file_submit._SubmitResponse__response200(json_response, 200))
        self.assertEqual(result, {})
        self.assertEqual(status_code, 500)
        mock_logging.assert_called_once()

    def test_response_methods_scenarios(self):
        test_cases = [
            ('_SubmitResponse__response400', {"error": "Invalid API key"}, {"error": "Invalid API key"}, 400),
            ('_SubmitResponse__response401', {}, {}, 401),
            ('_SubmitResponse__response422', {"error": "Unprocessable Entity"}, {"error": "Unprocessable Entity"}, 422)
        ]
        
        for method_name, json_response, expected_result, expected_status in test_cases:
            with self.subTest(method=method_name):
                method = getattr(self.file_submit, method_name)
                result, status_code = asyncio.run(method(json_response, expected_status))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    def test_http_responses_mapping(self):
        test_cases = [
            ("429", self.file_submit._SubmitResponse__response401),
            ("411", self.file_submit._SubmitResponse__response422)
        ]
        
        for status_code, expected_method in test_cases:
            with self.subTest(status_code=status_code):
                actual_method = self.file_submit._http_responses[status_code]
                self.assertEqual(actual_method, expected_method)

    def test_handle_response_scenarios(self):
        test_cases = [
            (200, {"data_id": "test_id"}, 200),
            (400, {"error": "Bad request"}, 400),
            (401, {}, 401),
            (422, {"error": "Unprocessable"}, 422),
            (429, {}, 401),
            (411, {"error": "Length Required"}, 422)
        ]
        
        for status_code, json_response, expected_status in test_cases:
            with self.subTest(status_code=status_code):
                result, actual_status = asyncio.run(self.file_submit.handle_response(json_response, status_code))
                self.assertEqual(actual_status, expected_status)
                self.assertIsInstance(result, dict)

    def test_handle_response_invalid_status(self):
        with self.assertRaises(ValueError) as context:
            asyncio.run(self.file_submit.handle_response({}, 999))
        
        self.assertIn("Not Allowed: 999 response code not allowed", str(context.exception))

    def test_translate_and_default_methods(self):
        translation = {'field': '{0}', 'other': 'static'}
        self.file_submit._translate('field', translation, 'test_value')
        self.assertEqual(translation['field'], 'test_value')
        self.assertEqual(translation['other'], 'static')
        
        json_response = {"test": "data"}
        result, status_code = asyncio.run(self.file_submit._default_response(json_response, 200))
        self.assertEqual(result, json_response)
        self.assertEqual(status_code, 200)

    def test_initialization_scenarios(self):
        test_cases = [
            ('', ''),
            ('test_api_key', 'test_api_key')
        ]
        
        for apikey, expected_apikey in test_cases:
            submit_response = SubmitResponse(apikey)
            self.assertEqual(submit_response._apikey, expected_apikey)

    def test_allowed_responses_completeness(self):
        expected_codes = [200, 400, 401, 411, 422, 429, 500, 503]
        self.assertEqual(set(self.file_submit._allowed_responses), set(expected_codes))
        
        for code in expected_codes:
            self.assertIn(str(code), self.file_submit._http_responses)


if __name__ == '__main__':
    unittest.main()