import unittest
from unittest.mock import patch, Mock
import asyncio
import os
import sys
import logging
import json
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.responses.sanitized_file import SanitizedFile  

class TestRetrieveSanitized(unittest.TestCase):

    def setUp(self):
        self.retrieve_sanitized = SanitizedFile()

    def test_init(self):
        """Test initialization and inheritance"""
        self.assertIsInstance(self.retrieve_sanitized, BaseResponse)
        self.assertEqual(self.retrieve_sanitized._allowed_responses, [200, 204, 401, 403, 404, 405, 500])
        self.assertIn("204", self.retrieve_sanitized._http_responses)
        self.assertIn("401", self.retrieve_sanitized._http_responses)
        self.assertIn("403", self.retrieve_sanitized._http_responses)
        self.assertIn("404", self.retrieve_sanitized._http_responses)
        self.assertIn("405", self.retrieve_sanitized._http_responses)

    def test_response_methods_scenarios(self):
        """Test all response methods efficiently"""
        test_cases = [
            # (method_name, response_data, expected_result, expected_status)
            ('_SanitizedFile__response204', {"test": "data"}, {"test": "data"}, 204),
            ('_SanitizedFile__response401', {"error": "Unauthorized"}, {}, 401),
            ('_SanitizedFile__response403', {"error": "Forbidden"}, {"error": "Forbidden"}, 403),
            ('_SanitizedFile__response501', {"error": "Method Not Allowed"}, {"error": "Method Not Allowed"}, 501),
        ]
        
        for method_name, response_data, expected_result, expected_status in test_cases:
            with self.subTest(method=method_name):
                method = getattr(self.retrieve_sanitized, method_name)
                result, status_code = asyncio.run(method(response_data, expected_status))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    def test_response400_scenarios(self):
        """Test response400 method with different input types"""
        test_cases = [
            # (response_data, expected_result, expected_status)
            ({"error": "Not Found"}, {"error": "Not Found"}, 400),  # Dict input
            (b'{"error": "Not Found"}', {"error": "Not Found"}, 400),  # Bytes input
            (bytearray(b'{"error": "Not Found"}'), {"error": "Not Found"}, 400),  # Bytearray input
            (b'invalid json', b'invalid json', 400),  # Invalid JSON bytes
            ("string response", "string response", 400),  # String input
        ]
        
        for response_data, expected_result, expected_status in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, expected_status)

    def test_http_responses_mapping(self):
        """Test HTTP response mappings"""
        test_cases = [
            # (status_code, expected_method)
            ("204", self.retrieve_sanitized._SanitizedFile__response204),
            ("401", self.retrieve_sanitized._SanitizedFile__response401),
            ("403", self.retrieve_sanitized._SanitizedFile__response403),
            ("404", self.retrieve_sanitized._SanitizedFile__response400),  # 404 maps to response400
            ("405", self.retrieve_sanitized._SanitizedFile__response501),  # 405 maps to response501
        ]
        
        for status_code, expected_method in test_cases:
            with self.subTest(status_code=status_code):
                actual_method = self.retrieve_sanitized._http_responses[status_code]
                self.assertEqual(actual_method, expected_method)

    def test_handle_response_scenarios(self):
        """Test handle_response method scenarios"""
        test_cases = [
            # (status_code, response_data, expected_status)
            (200, {"data": "test"}, 200),  # Default response
            (204, {"test": "data"}, 204),
            (401, {"error": "Unauthorized"}, 401),
            (403, {"error": "Forbidden"}, 403),
            (404, {"error": "Not Found"}, 400),  # 404 maps to 400
            (405, {"error": "Method Not Allowed"}, 501),  # 405 maps to 501
            (500, {"error": "Internal Server Error"}, 500),  # Default response
        ]
        
        for status_code, response_data, expected_status in test_cases:
            with self.subTest(status_code=status_code):
                result, actual_status = asyncio.run(self.retrieve_sanitized.handle_response(response_data, status_code))
                self.assertEqual(actual_status, expected_status)
                self.assertIsNotNone(result)

    def test_handle_response_invalid_status(self):
        """Test handle_response with invalid status code"""
        with self.assertRaises(ValueError) as context:
            asyncio.run(self.retrieve_sanitized.handle_response({}, 999))
        
        self.assertIn("Not Allowed: 999 response code not allowed", str(context.exception))

    def test_default_response_method(self):
        """Test the default response method"""
        response_data = {"test": "data"}
        result, status_code = asyncio.run(self.retrieve_sanitized._default_response(response_data, 200))
        self.assertEqual(result, response_data)
        self.assertEqual(status_code, 200)

    def test_apikey_initialization(self):
        """Test initialization with custom apikey"""
        custom_apikey = "test_api_key"
        sanitized_file = SanitizedFile(custom_apikey)
        self.assertEqual(sanitized_file._apikey, custom_apikey)

    def test_allowed_responses_completeness(self):
        """Test that all expected response codes are allowed"""
        expected_codes = [200, 204, 401, 403, 404, 405, 500]
        self.assertEqual(set(self.retrieve_sanitized._allowed_responses), set(expected_codes))
        
        # Verify all codes have corresponding response methods or use default
        for code in expected_codes:
            if str(code) in self.retrieve_sanitized._http_responses:
                self.assertIsNotNone(self.retrieve_sanitized._http_responses[str(code)])

    def test_response400_json_parsing_edge_cases(self):
        """Test response400 JSON parsing edge cases"""
        test_cases = [
            # (response_data, expected_result)
            (b'{"valid": "json"}', {"valid": "json"}),
            (b'{"nested": {"key": "value"}}', {"nested": {"key": "value"}}),
            (b'[]', []),  # Empty array
            (b'{}', {}),  # Empty object
            (b'null', None),  # Null value
            (b'"string"', "string"),  # String value
            (b'123', 123),  # Number value
        ]
        
        for response_data, expected_result in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                self.assertEqual(result, expected_result)
                self.assertEqual(status_code, 400)

    def test_response400_invalid_json_handling(self):
        """Test response400 handling of invalid JSON"""
        test_cases = [
            b'invalid json string',
            b'{invalid json}',
            b'{"incomplete": json',
            b'not json at all',
            b'',
        ]
        
        for response_data in test_cases:
            with self.subTest(response_data=response_data):
                result, status_code = asyncio.run(self.retrieve_sanitized._SanitizedFile__response400(response_data, 400))
                # Should return the original bytes when JSON parsing fails
                self.assertEqual(result, response_data)
                self.assertEqual(status_code, 400)


if __name__ == '__main__':
    unittest.main()