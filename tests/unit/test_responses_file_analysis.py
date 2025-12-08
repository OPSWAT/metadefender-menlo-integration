import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse
from metadefender_menlo.api.responses.file_analysis import FileAnalyis

class TestFileAnalysis(unittest.TestCase):

    def setUp(self):
        self.file_analysis = FileAnalyis()

    def test_init(self):
        self.assertIsInstance(self.file_analysis, BaseResponse)
        self.assertEqual(self.file_analysis._allowed_responses, [200, 400, 401, 404, 500])
        for code in ["200", "400", "401", "404"]:
            self.assertIn(code, self.file_analysis._http_responses)

    def test_model_outcome_scenarios(self):
        test_cases = [
            ('pending', {}, 'unknown'),
            ('completed', {'process_info': {'profile': 'cdr'}, 'sanitized': {'result': 'Allowed'}}, 'clean'),
            ('completed', {'process_info': {'profile': 'sanitize'}, 'sanitized': {'result': 'Error'}}, 'error'),
            ('completed', {'process_info': {'profile': 'sanitize'}, 'sanitized': {'result': 'unknown'}}, 'unknown'),
            ('completed', {'process_info': {'profile': 'sanitize'}, 'sanitized': {'result': 'Infected'}}, 'infected'),
            ('completed', {'process_info': {'profile': 'other', 'result': 'Allowed'}}, 'clean'),
            ('completed', {'process_info': {'profile': 'other', 'result': 'Blocked'}}, 'infected'),
            ('completed', {'process_info': {'profile': 'cdr'}}, 'infected')
        ]
        
        for result, json_response, expected in test_cases:
            with self.subTest(result=result, json_response=json_response):
                self.assertEqual(self.file_analysis.model_outcome(result, json_response), expected)

    def test_check_analysis_complete_scenarios(self):
        test_cases = [
            ({'process_info': {'progress_percentage': 100}, 'sanitized': {'progress_percentage': 100}}, True),
            ({'process_info': {'progress_percentage': 90}, 'sanitized': {'progress_percentage': 100}}, False),
            ({'process_info': {'progress_percentage': 100}, 'sanitized': {'progress_percentage': 90}}, False),
            ({'process_info': {'progress_percentage': 100}}, True),
            ({'sanitized': {'progress_percentage': 100}}, False),
            ({}, False)
        ]
        
        for json_response, expected in test_cases:
            with self.subTest(json_response=json_response):
                self.assertEqual(self.file_analysis.check_analysis_complete(json_response), expected)

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_response200_scenarios(self, mock_get_instance):
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
                        'details': [{'action': 'Remove', 'count': 1, 'object_name': 'Macro'}]
                    }
                },
                'profile': 'cdr'
            },
            'sanitized': {'progress_percentage': 100, 'result': 'Allowed'}
        }
        
        result, status_code = asyncio.run(self.file_analysis._FileAnalyis__response200(json_response, 200))
        self.assertEqual(status_code, 200)
        self.assertEqual(result['result'], 'completed')
        self.assertEqual(result['outcome'], 'clean')
        self.assertEqual(result['report_url'], 'https://example.com/123')

        result, status_code = asyncio.run(self.file_analysis._FileAnalyis__response200({}, 200))
        self.assertEqual(status_code, 404)
        self.assertEqual(result, {})

    @patch('logging.error')
    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_response200_exception(self, mock_get_instance, mock_logging):
        mock_get_instance.side_effect = Exception("Test error")
        json_response = {'data_id': '123'}
        
        result, status_code = asyncio.run(self.file_analysis._FileAnalyis__response200(json_response, 200))
        self.assertEqual(status_code, 500)
        self.assertEqual(result, {})
        mock_logging.assert_called_once()

    def test_response_methods(self):
        test_cases = [
            ('_FileAnalyis__response400', {}, 400, {}, 400),
            ('_FileAnalyis__response401', {}, 401, {}, 401)
        ]
        
        for method_name, response, status_code, expected_result, expected_status in test_cases:
            method = getattr(self.file_analysis, method_name)
            result, status = asyncio.run(method(response, status_code))
            self.assertEqual(result, expected_result)
            self.assertEqual(status, expected_status)

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_extract_filename_scenarios(self, mock_get_instance):
        mock_api = Mock()
        mock_api.get_sanitized_file_headers = AsyncMock(return_value={})
        mock_get_instance.return_value = mock_api

        test_cases = [
            ({'data_id': '123', 'file_info': {'display_name': 'test%20file.txt'}}, 'test file.txt'),
            ({'data_id': '123', 'file_info': {'display_name': 'test.txt'}, 'sanitized': {'result': 'Allowed'}, 
              'process_info': {'post_processing': {'actions_ran': 'Sanitized'}}}, 'sanitized_test.txt'),
            ({}, "")
        ]
        
        for json_response, expected in test_cases:
            with self.subTest(json_response=json_response):
                result = asyncio.run(self.file_analysis._extract_filename(json_response))
                self.assertEqual(result, expected)

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_extract_filename_from_headers(self, mock_get_instance):
        test_cases = [
            ({'content-disposition': 'attachment; filename="test%20file.txt"'}, 'test file.txt'),
            ({'content-disposition': 'attachment; filename="test.txt"'}, 'test.txt'),
            ({'content-disposition': 'attachment'}, None),
            ({}, None)
        ]
        
        for headers, expected in test_cases:
            with self.subTest(headers=headers):
                result = asyncio.run(self.file_analysis._extract_filename_from_headers(headers))
                self.assertEqual(result, expected)

    def test_update_sanitization_details_scenarios(self):
        model = FileAnalysisResponse()
        
        test_cases = [
            ({
                'sanitization_details': {
                    'details': [
                        {'action': 'Remove', 'count': 1, 'object_name': 'Macro'},
                        {'action': 'Clean', 'count': 2, 'object_name': 'Metadata'},
                        {'action': 'Modify'}
                    ]
                }
            }, [
                "Action: Remove - Count: 1 - Object type: Macro",
                "Action: Clean - Count: 2 - Object type: Metadata",
                "Action: Modify - Count: All - Object type: All"
            ]),
            ({'sanitization_details': {'details': "Some string details"}}, ["Some string details"]),
            ({'sanitization_details': {'details': []}}, [])
        ]
        
        for post_process, expected in test_cases:
            self.file_analysis._update_sanitization_details(model, post_process)
            self.assertEqual(model.modifications, expected)

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_initialize_model_scenarios(self, mock_get_instance):
        mock_api = Mock()
        mock_api.report_url = "https://example.com/{data_id}"
        mock_api.get_sanitized_file_path = Mock(return_value="/path/to/file")
        mock_get_instance.return_value = mock_api

        test_cases = [
            ({
                'data_id': '123',
                'file_info': {'display_name': 'test.txt'},
                'process_info': {'progress_percentage': 100, 'profile': 'cdr'},
                'sanitized': {'progress_percentage': 100, 'result': 'Allowed'}
            }, 'completed', 'clean'),
            ({
                'data_id': '123',
                'file_info': {'display_name': 'test.txt'},
                'process_info': {'progress_percentage': 50, 'profile': 'cdr'},
                'sanitized': {'progress_percentage': 100, 'result': 'Allowed'}
            }, 'pending', 'unknown')
        ]
        
        for json_response, expected_result, expected_outcome in test_cases:
            model = asyncio.run(self.file_analysis._initialize_model(json_response))
            self.assertEqual(model.result, expected_result)
            self.assertEqual(model.outcome, expected_outcome)
            self.assertEqual(model.report_url, 'https://example.com/123')

    @patch('metadefender_menlo.api.metadefender.metadefender_api.MetaDefenderAPI.get_instance')
    def test_initialize_model_exception(self, mock_get_instance):
        mock_api = Mock()
        mock_api.report_url = "https://example.com/{data_id}"
        mock_api.get_sanitized_file_path = Mock(side_effect=Exception("Test error"))
        mock_get_instance.return_value = mock_api

        json_response = {
            'data_id': '123',
            'file_info': {'display_name': 'test.txt'},
            'process_info': {'progress_percentage': 100, 'profile': 'cdr'},
            'sanitized': {'progress_percentage': 100, 'result': 'Allowed'}
        }
        
        model = asyncio.run(self.file_analysis._initialize_model(json_response))
        self.assertIsNone(model.sanitized_file_path)


if __name__ == '__main__':
    unittest.main()