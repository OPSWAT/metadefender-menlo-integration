import unittest
from unittest.mock import AsyncMock
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse


class TestBaseResponse(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        BaseResponse._allowed_responses = []
        BaseResponse._http_responses = {}

    def test_initialization_scenarios(self):
        test_cases = [
            (['test_key', [200, 400]], {'allowed': [200, 400], 'apikey': 'test_key', 'responses_count': 2}),
            (['', []], {'allowed': [], 'apikey': '', 'responses_count': 0}),
            (['', [200]], {'allowed': [200], 'apikey': '', 'responses_count': 1})
        ]
        
        for args, expected in test_cases:
            BaseResponse._http_responses = {}
            base_response = BaseResponse(*args)
            self.assertEqual(base_response._allowed_responses, expected['allowed'])
            self.assertEqual(base_response._apikey, expected['apikey'])
            self.assertEqual(len(base_response._http_responses), expected['responses_count'])
            
            for code in expected['allowed']:
                self.assertIn(str(code), base_response._http_responses)

    def test_initialization_error_cases(self):
        with self.assertRaises(TypeError):
            BaseResponse(allowed_responses=None)

    async def test_handle_response_scenarios(self):
        base_response = BaseResponse(allowed_responses=[200])
        
        result, status = await base_response.handle_response({'data': 'test'}, 200)
        self.assertEqual(result, {'data': 'test'})
        self.assertEqual(status, 200)
        
        with self.assertRaises(ValueError) as context:
            await base_response.handle_response({}, 404)
        self.assertIn('Not Allowed: 404 response code not allowed', str(context.exception))

    async def test_custom_handler(self):
        base_response = BaseResponse(allowed_responses=[200])
        
        custom_handler = AsyncMock(return_value=({'custom': 'data'}, 201))
        base_response._http_responses['200'] = custom_handler
        
        result, status = await base_response.handle_response({}, 200)
        
        self.assertEqual(result, {'custom': 'data'})
        self.assertEqual(status, 201)
        custom_handler.assert_called_once_with({}, 200)

    async def test_default_response(self):
        base_response = BaseResponse(allowed_responses=[200])
        
        test_cases = [
            ({'test': 'data'}, 200),
            ({'test': 'data'}, 201)
        ]
        
        for data, expected_status in test_cases:
            result, status = await base_response._default_response(data, expected_status)
            self.assertEqual(result, data)
            self.assertEqual(status, expected_status)

    def test_translate(self):
        base_response = BaseResponse(allowed_responses=[200])
        
        translation = {'field': 'Value: {0}'}
        base_response._translate('field', translation, 'test')
        self.assertEqual(translation['field'], 'Value: test')

    def test_class_variables_shared(self):
        self.assertEqual(BaseResponse._allowed_responses, [])
        self.assertEqual(BaseResponse._http_responses, {})
        
        BaseResponse(allowed_responses=[200])
        BaseResponse(allowed_responses=[400])
        
        self.assertEqual(len(BaseResponse._http_responses), 2)
        self.assertIn('200', BaseResponse._http_responses)
        self.assertIn('400', BaseResponse._http_responses)


if __name__ == '__main__':
    unittest.main()