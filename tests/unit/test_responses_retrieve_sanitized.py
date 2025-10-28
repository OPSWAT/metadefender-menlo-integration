import unittest
from unittest.mock import patch
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.responses.sanitized_file import SanitizedFile

class TestRetrieveSanitized(unittest.TestCase):

    def setUp(self):
        self.retrieve_sanitized = SanitizedFile()

    def test_init(self):
        self.assertIsInstance(self.retrieve_sanitized, BaseResponse)
        self.assertEqual(self.retrieve_sanitized._allowed_responses, [200, 204, 401, 403, 404, 405, 500])
        for code in ["204", "401", "403", "404", "405"]:
            self.assertIn(code, self.retrieve_sanitized._http_responses)

    def test_response_methods_scenarios(self):
        test_cases = [
            ('_SanitizedFile__response204', {"test": "data"}, {"test": "data"}, 204),
            ('_SanitizedFile__response401', {"error": "Unauthorized"}, {}, 401),
            ('_SanitizedFile__response403', {"error": "Forbidden"}, {"error": "Forbidden"}, 403),
            ('_SanitizedFile__response501', {"error": "Method Not Allowed"}, {"error": "Method Not Allowed"}, 501)
        ]
        
        for method_name, response_data, expected_result, expected_status in test_cases:
            with self.subTest(method=method_name):
                method = getattr(self.retrieve_sanitized, method_name)
                result, status_code = asyncio.run(method(response_data, expected_status))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    def test_response400_scenarios(self):
        test_cases = [
            ({"error": "Not Found"}, {"error": "Not Found"}, 400),
            (b'{"error": "Not Found"}', {"error": "Not Found"}, 400),
            (bytearray(b'{"error": "Not Found"}'), {"error": "Not Found"}, 400),
            (b'invalid json', b'invalid json', 400),
            ("string response", "string response", 400)
        ]
        
        for response_data, expected_result, expected_status in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    def test_response400_json_parsing_edge_cases(self):
        test_cases = [
            (b'{"valid": "json"}', {"valid": "json"}),
            (b'{"nested": {"key": "value"}}', {"nested": {"key": "value"}}),
            (b'[]', []),
            (b'{}', {}),
            (b'null', None),
            (b'"string"', "string"),
            (b'123', 123)
        ]
        
        for response_data, expected_result in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, 400)

    def test_response400_invalid_json_handling(self):
        test_cases = [
            b'invalid json string',
            b'{invalid json}',
            b'{"incomplete": json',
            b'not json at all',
            b''
        ]
        
        for response_data in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                self.assertEqual(result, response_data)
                self.assertEqual(status_code, 400)

    def test_http_responses_mapping(self):
        test_cases = [
            ("204", self.retrieve_sanitized._SanitizedFile__response204),
            ("401", self.retrieve_sanitized._SanitizedFile__response401),
            ("403", self.retrieve_sanitized._SanitizedFile__response403),
            ("404", self.retrieve_sanitized._SanitizedFile__response400),
            ("405", self.retrieve_sanitized._SanitizedFile__response501)
        ]
        
        for status_code, expected_method in test_cases:
            with self.subTest(status_code=status_code):
                actual_method = self.retrieve_sanitized._http_responses[status_code]
                self.assertEqual(actual_method, expected_method)

    def test_handle_response_scenarios(self):
        test_cases = [
            (200, {"data": "test"}, 200),
            (204, {"test": "data"}, 204),
            (401, {"error": "Unauthorized"}, 401),
            (403, {"error": "Forbidden"}, 403),
            (404, {"error": "Not Found"}, 400),
            (405, {"error": "Method Not Allowed"}, 501),
            (500, {"error": "Internal Server Error"}, 500)
        ]
        
        for status_code, response_data, expected_status in test_cases:
            with self.subTest(status_code=status_code):
                result, actual_status = asyncio.run(self.retrieve_sanitized.handle_response(response_data, status_code))
                self.assertEqual(actual_status, expected_status)
                self.assertIsNotNone(result)

    def test_handle_response_invalid_status(self):
        with self.assertRaises(ValueError) as context:
            asyncio.run(self.retrieve_sanitized.handle_response({}, 999))
        
        self.assertIn("Not Allowed: 999 response code not allowed", str(context.exception))

    def test_initialization_scenarios(self):
        test_cases = [
            ('', ''),
            ('test_api_key', 'test_api_key')
        ]
        
        for apikey, expected_apikey in test_cases:
            sanitized_file = SanitizedFile(apikey)
            self.assertEqual(sanitized_file._apikey, expected_apikey)

    def test_default_response_and_completeness(self):
        response_data = {"test": "data"}
        result, status_code = asyncio.run(self.retrieve_sanitized._default_response(response_data, 200))
        self.assertEqual(result, response_data)
        self.assertEqual(status_code, 200)
        
        expected_codes = [200, 204, 401, 403, 404, 405, 500]
        self.assertEqual(set(self.retrieve_sanitized._allowed_responses), set(expected_codes))
        
        for code in expected_codes:
            if str(code) in self.retrieve_sanitized._http_responses:
                self.assertIsNotNone(self.retrieve_sanitized._http_responses[str(code)])


if __name__ == '__main__':
    unittest.main()