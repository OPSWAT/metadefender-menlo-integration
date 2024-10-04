import unittest
from unittest.mock import Mock, patch
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse
from metadefender_menlo.api.responses.file_analysis import FileAnalyis

class TestFileAnalysis(unittest.TestCase):

    def setUp(self):
        self.file_analysis = FileAnalyis()

    def test_init(self):
        self.assertIsInstance(self.file_analysis, BaseResponse)
        self.assertEqual(self.file_analysis._allowed_responses, [200, 400, 401, 404, 500])
        self.assertIn("200", self.file_analysis._http_responses)
        self.assertIn("400", self.file_analysis._http_responses)
        self.assertIn("401", self.file_analysis._http_responses)
        self.assertIn("404", self.file_analysis._http_responses)

    def test_model_outcome_completed_cdr_allowed(self):
        json_response = {
            'process_info': {'profile': 'cdr'},
            'sanitized': {'result': 'Allowed'}
        }
        result = self.file_analysis.model_outcome('completed', json_response)
        self.assertEqual(result, 'clean')

    def test_model_outcome_completed_sanitize_error(self):
        json_response = {
            'process_info': {'profile': 'sanitize'},
            'sanitized': {'result': 'Error'}
        }
        result = self.file_analysis.model_outcome('completed', json_response)
        self.assertEqual(result, 'error')

    def test_model_outcome_not_completed(self):
        result = self.file_analysis.model_outcome('pending', {})
        self.assertEqual(result, 'unknown')

    def test_check_analysis_complete_true(self):
        json_response = {
            'process_info': {'progress_percentage': 100},
            'sanitized': {'progress_percentage': 100}
        }
        result = self.file_analysis.check_analysis_complete(json_response)
        self.assertTrue(result)

    def test_check_analysis_complete_false(self):
        json_response = {
            'process_info': {'progress_percentage': 90},
            'sanitized': {'progress_percentage': 100}
        }
        result = self.file_analysis.check_analysis_complete(json_response)
        self.assertFalse(result)

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_response200_success(self, mock_get_instance):
        mock_api = Mock()
        mock_api.report_url = "https://example.com/{data_id}"
        mock_get_instance.return_value = mock_api

        json_response = {
            'data_id': '123',
            'file_info': {'display_name': 'test.txt'},
            'process_info': {
                'progress_percentage': 100,
                'post_processing': {
                    'sanitization_details': {
                        'details': [
                            {'action': 'Remove', 'count': 1, 'object_name': 'Macro'}
                        ]
                    }
                },
                'profile': 'cdr'
            },
            'sanitized': {'progress_percentage': 100, 'result': 'Allowed'}
        }
        
        result, status_code = self.file_analysis._FileAnalyis__response200(json_response, 200)
        
        self.assertEqual(status_code, 200)
        self.assertEqual(result['result'], 'completed')
        self.assertEqual(result['outcome'], 'clean')
        self.assertEqual(result['report_url'], 'https://example.com/123')
        self.assertEqual(result['filename'], 'test.txt')
        self.assertEqual(result['modifications'], ['Action: Remove - Count: 1 - Object type: Macro'])

    def test_response200_no_data_id(self):
        json_response = {}
        result, status_code = self.file_analysis._FileAnalyis__response200(json_response, 200)
        self.assertEqual(status_code, 404)
        self.assertEqual(result, {})

    @patch('logging.error')
    def test_response200_exception(self, mock_logging):
        json_response = {'data_id': '123'}
        result, status_code = self.file_analysis._FileAnalyis__response200(json_response, 200)
        self.assertEqual(status_code, 500)
        self.assertEqual(result, {})
        mock_logging.assert_called_once()

    def test_response400(self):
        result, status_code = self.file_analysis._FileAnalyis__response400({}, 400)
        self.assertEqual(status_code, 400)
        self.assertEqual(result, {})

    def test_response401(self):
        result, status_code = self.file_analysis._FileAnalyis__response401({}, 401)
        self.assertEqual(status_code, 401)
        self.assertEqual(result, {})

    def test_extract_filename_success(self):
        json_response = {'file_info': {'display_name': 'test%20file.txt'}}
        result = self.file_analysis._extract_filename(json_response)
        self.assertEqual(result, 'test file.txt')

    def test_extract_filename_exception(self):
        json_response = {}
        result = self.file_analysis._extract_filename(json_response)
        self.assertEqual(result, "")

    def test_populate(self):
        model = FileAnalysisResponse()
        post_process = {
            'sanitization_details': {
                'details': [
                    {'action': 'Remove', 'count': 1, 'object_name': 'Macro'},
                    {'action': 'Clean', 'count': 2, 'object_name': 'Metadata'}
                ]
            }
        }
        self.file_analysis._populate(model, post_process)
        expected_modifications = [
            "Action: Remove - Count: 1 - Object type: Macro",
            "Action: Clean - Count: 2 - Object type: Metadata"
        ]
        self.assertEqual(model.modifications, expected_modifications)

    def test_populate_with_string_details(self):
        model = FileAnalysisResponse()
        post_process = {
            'sanitization_details': {
                'details': "Some string details"
            }
        }
        self.file_analysis._populate(model, post_process)
        self.assertEqual(model.modifications, ["Some string details"])

    def test_model_outcome_completed_sanitize_unknown(self):
        json_response = {
            'process_info': {'profile': 'sanitize'},
            'sanitized': {'result': 'unknown'}
        }
        result = self.file_analysis.model_outcome('completed', json_response)
        self.assertEqual(result, 'unknown')

    def test_model_outcome_completed_sanitize_infected(self):
        json_response = {
            'process_info': {'profile': 'sanitize'},
            'sanitized': {'result': 'Infected'}
        }
        result = self.file_analysis.model_outcome('completed', json_response)
        self.assertEqual(result, 'infected')

if __name__ == '__main__':
    unittest.main()

