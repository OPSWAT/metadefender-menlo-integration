import unittest

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.responses.sanitized_file import SanitizedFile  

class TestRetrieveSanitized(unittest.TestCase):

    def setUp(self):
        self.retrieve_sanitized = SanitizedFile()

    def test_init(self):
        self.assertIsInstance(self.retrieve_sanitized, BaseResponse)
        self.assertEqual(self.retrieve_sanitized._allowed_responses, [200, 204, 401, 403, 404, 405, 500])
        self.assertIn("204", self.retrieve_sanitized._http_responses)
        self.assertIn("403", self.retrieve_sanitized._http_responses)
        self.assertIn("404", self.retrieve_sanitized._http_responses)
        self.assertIn("405", self.retrieve_sanitized._http_responses)
        self.assertIn("401", self.retrieve_sanitized._http_responses)

    def test_response204(self):
        response = {"test": "data"}
        result, status_code = self.retrieve_sanitized._RetrieveSanitized__response204(response, 204)
        self.assertEqual(result, response)
        self.assertEqual(status_code, 204)

    def test_response400(self):
        response = {"error": "Not Found"}
        result, status_code = self.retrieve_sanitized._RetrieveSanitized__response400(response, 404)
        self.assertEqual(result, response)
        self.assertEqual(status_code, 400)

    def test_response401(self):
        response = {"error": "Unauthorized"}
        result, status_code = self.retrieve_sanitized._RetrieveSanitized__response401(response, 401)
        self.assertEqual(result, {})
        self.assertEqual(status_code, 401)

    def test_response403(self):
        response = {"error": "Forbidden"}
        result, status_code = self.retrieve_sanitized._RetrieveSanitized__response403(response, 403)
        self.assertEqual(result, response)
        self.assertEqual(status_code, 403)

    def test_response501(self):
        response = {"error": "Method Not Allowed"}
        result, status_code = self.retrieve_sanitized._RetrieveSanitized__response501(response, 405)
        self.assertEqual(result, response)
        self.assertEqual(status_code, 501)

    def test_http_responses_mapping(self):
        self.assertEqual(self.retrieve_sanitized._http_responses["204"], self.retrieve_sanitized._RetrieveSanitized__response204)
        self.assertEqual(self.retrieve_sanitized._http_responses["403"], self.retrieve_sanitized._RetrieveSanitized__response403)
        self.assertEqual(self.retrieve_sanitized._http_responses["404"], self.retrieve_sanitized._RetrieveSanitized__response400)
        self.assertEqual(self.retrieve_sanitized._http_responses["405"], self.retrieve_sanitized._RetrieveSanitized__response501)
        self.assertEqual(self.retrieve_sanitized._http_responses["401"], self.retrieve_sanitized._RetrieveSanitized__response401)

if __name__ == '__main__':
    unittest.main()