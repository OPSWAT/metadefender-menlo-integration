import unittest
from unittest.mock import patch
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.check_existing import CheckExisting


class TestCheckExisting(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        CheckExisting._allowed_responses = []
        CheckExisting._http_responses = {}

    def test_initialization(self):
        test_cases = [
            ('test_key', 'test_key'),
            ('', '')
        ]
        
        for apikey, expected_apikey in test_cases:
            CheckExisting._http_responses = {}
            check_existing = CheckExisting(apikey=apikey)
            self.assertEqual(check_existing._allowed_responses, [200, 400, 401, 404, 500])
            self.assertEqual(check_existing._apikey, expected_apikey)
            self.assertEqual(len(check_existing._http_responses), 5)
            
            for code in ['200', '400', '401', '404', '500']:
                self.assertIn(code, check_existing._http_responses)

    async def test_response200_scenarios(self):
        check_existing = CheckExisting()
        
        test_cases = [
            ({'data_id': 'test_id'}, 200, {'uuid': 'test_id', 'result': 'found'}, 200),
            ({}, 200, {}, 404),
            ('invalid', 200, 'invalid', 404),
            (None, 200, {}, 500)
        ]
        
        for response, status_code, expected_result, expected_status in test_cases:
            if response is None:
                with patch('metadefender_menlo.api.responses.check_existing.logging.error') as mock_logging:
                    result, status = await check_existing._CheckExisting__response200(response, status_code)
                    self.assertEqual(result, expected_result)
                    self.assertEqual(status, expected_status)
                    mock_logging.assert_called_once()
            else:
                result, status = await check_existing._CheckExisting__response200(response, status_code)
                self.assertEqual(result, expected_result)
                self.assertEqual(status, expected_status)

    async def test_response200_with_exception(self):
        check_existing = CheckExisting()
        
        with patch.object(check_existing, '_translate', side_effect=Exception('Test error')):
            with patch('metadefender_menlo.api.responses.check_existing.logging.error') as mock_logging:
                result, status_code = await check_existing._CheckExisting__response200({'data_id': 'test'}, 200)
                
                self.assertEqual(result, {})
                self.assertEqual(status_code, 500)
                mock_logging.assert_called_once()

    async def test_response_methods(self):
        check_existing = CheckExisting()
        
        test_cases = [
            ('_CheckExisting__response400', {'sha256': 'test_hash'}, 400, {'uuid': 'test_hash', 'result': '404'}, 200),
            ('_CheckExisting__response401', {}, 401, {}, 401)
        ]
        
        for method_name, response, status_code, expected_result, expected_status in test_cases:
            method = getattr(check_existing, method_name)
            result, status = await method(response, status_code)
            self.assertEqual(result, expected_result)
            self.assertEqual(status, expected_status)

    async def test_handle_response_scenarios(self):
        check_existing = CheckExisting()
        
        result, status_code = await check_existing.handle_response({'data_id': 'test_id'}, 200)
        self.assertEqual(result, {'uuid': 'test_id', 'result': 'found'})
        self.assertEqual(status_code, 200)
        
        with self.assertRaises(ValueError):
            await check_existing.handle_response({}, 999)


if __name__ == '__main__':
    unittest.main()