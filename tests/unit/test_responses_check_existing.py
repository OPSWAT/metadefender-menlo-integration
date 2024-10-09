import unittest
from unittest.mock import patch
from metadefender_menlo.api.responses.check_existing import CheckExisting
from metadefender_menlo.api.responses.base_response import BaseResponse


class TestCheckExisting(unittest.TestCase):

    def setUp(self):
        self.check_existing = CheckExisting()

    def test_init(self):
        self.assertIsInstance(self.check_existing, BaseResponse)
        self.assertEqual(self.check_existing._allowed_responses, [200, 400, 401, 404, 500])
        self.assertIn("200", self.check_existing._http_responses)
        self.assertIn("400", self.check_existing._http_responses)
        self.assertIn("401", self.check_existing._http_responses)
        self.assertIn("404", self.check_existing._http_responses)

    def test_response200_with_data_id(self):
        response = {"data_id": "test_id"}
        result, status_code = self.check_existing._CheckExisting__response200(response, 200)
        self.assertEqual(result, {"uuid": "test_id", "result": "found"})
        self.assertEqual(status_code, 200)

    def test_response200_without_data_id(self):
        response = {}
        result, status_code = self.check_existing._CheckExisting__response200(response, 200)
        self.assertEqual(result, {})
        self.assertEqual(status_code, 404)

    def test_response400(self):
        response = {"sha256": "test_sha256"}
        result, status_code = self.check_existing._CheckExisting__response400(response, 400)
        self.assertEqual(result, {"uuid": "test_sha256", "result": "404"})
        self.assertEqual(status_code, 200)

    def test_response401(self):
        response = {}
        result, status_code = self.check_existing._CheckExisting__response401(response, 401)
        self.assertEqual(result, {})
        self.assertEqual(status_code, 401)

    @patch('metadefender_menlo.api.responses.check_existing.logging.error')
    def test_response200_exception_handling(self, mock_logging_error):
        response = None
        result, status_code = self.check_existing._CheckExisting__response200(response, 200)

        self.assertEqual(result, {})
        self.assertEqual(status_code, 500)

        mock_logging_error.assert_called_once()

        log_message = mock_logging_error.call_args[0][0]
        self.assertIn("error", log_message)
        self.assertIn("MdCloudResponse", log_message)

if __name__ == '__main__':
    unittest.main()
