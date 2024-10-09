import unittest
from unittest.mock import patch
from metadefender_menlo.api.responses.file_submit import FileSubmit
from metadefender_menlo.api.responses.base_response import BaseResponse

class TestFileSubmit(unittest.TestCase):

    def setUp(self):
        self.file_submit = FileSubmit()

    def test_init(self):
        self.assertIsInstance(self.file_submit, BaseResponse)
        self.assertEqual(self.file_submit._allowed_responses, [200, 400, 401, 411, 422, 429, 500, 503])
        self.assertIn("200", self.file_submit._http_responses)
        self.assertIn("400", self.file_submit._http_responses)
        self.assertIn("401", self.file_submit._http_responses)
        self.assertIn("429", self.file_submit._http_responses)
        self.assertIn("411", self.file_submit._http_responses)

    def test_response200_with_data_id(self):
        json_response = {"data_id": "test_id"}
        result, status_code = self.file_submit._FileSubmit__response200(json_response, 200)
        self.assertEqual(result, {"uuid": "test_id", "result": "accepted"})
        self.assertEqual(status_code, 200)

    def test_response200_without_data_id(self):
        json_response = {}
        result, status_code = self.file_submit._FileSubmit__response200(json_response, 200)
        self.assertEqual(result, {"result": "skip"})
        self.assertEqual(status_code, 200)

    def test_response400(self):
        json_response = {"error": "Invalid API key"}
        result, status_code = self.file_submit._FileSubmit__response400(json_response, 400)
        self.assertEqual(result, json_response)
        self.assertEqual(status_code, 400)

    def test_response401(self):
        json_response = {}
        result, status_code = self.file_submit._FileSubmit__response401(json_response, 401)
        self.assertEqual(result, {})
        self.assertEqual(status_code, 401)

    def test_response422(self):
        json_response = {"error": "Unprocessable Entity"}
        result, status_code = self.file_submit._FileSubmit__response422(json_response, 422)
        self.assertEqual(result, json_response)
        self.assertEqual(status_code, 422)

    @patch.object(BaseResponse, '_translate')
    def test_response200_translate_calls(self, mock_translate):
        json_response = {"data_id": "test_id"}
        self.file_submit._FileSubmit__response200(json_response, 200)
        mock_translate.assert_any_call('uuid', {'uuid': '{0}', 'result': '{0}'}, 'test_id')
        mock_translate.assert_any_call('result', {'uuid': '{0}', 'result': '{0}'}, 'accepted')

    def test_response429(self):
        json_response = {}
        result, status_code = self.file_submit._http_responses["429"](json_response, 429)
        self.assertEqual(result, {})
        self.assertEqual(status_code, 401)

    def test_response411(self):
        json_response = {"error": "Length Required"}
        result, status_code = self.file_submit._http_responses["411"](json_response, 411)
        self.assertEqual(result, json_response)
        self.assertEqual(status_code, 422)

    @patch.object(BaseResponse, '_translate')
    def test_response200_exception_handling(self, mock_translate):
        json_response = {"data_id": "test_id"}
        mock_translate.side_effect = Exception("Forced exception for testing")

        result, status_code = self.file_submit._FileSubmit__response200(json_response, 200)

        self.assertEqual(result, {})
        self.assertEqual(status_code, 500)
    

if __name__ == '__main__':
    unittest.main()