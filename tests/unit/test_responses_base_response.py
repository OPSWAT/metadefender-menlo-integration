import unittest
from unittest.mock import Mock

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.base_response import BaseResponse

class TestBaseResponse(unittest.TestCase):

    def test_init(self):
        allowed_responses = [200, 400, 404]
        base_response = BaseResponse(apikey='test_key', allowed_responses=allowed_responses)
        
        self.assertEqual(base_response._allowed_responses, allowed_responses)
        self.assertEqual(base_response._apikey, 'test_key')
        
        for code in allowed_responses:
            self.assertIn(str(code), base_response._http_responses)
            self.assertEqual(base_response._http_responses[str(code)], base_response._default_response)

    def test_handle_response_allowed(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        mock_response = {'key': 'value'}
        result, status_code = base_response.handle_response(200, mock_response)
        
        self.assertEqual(result, mock_response)
        self.assertEqual(status_code, 200)

    def test_handle_response_not_allowed(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        with self.assertRaises(Exception) as context:
            base_response.handle_response(404, {})
        
        self.assertIn('404 response code not allowed', str(context.exception))

    def test_handle_response_custom_handler(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        custom_handler = Mock(return_value=({'custom': 'response'}, 201))
        base_response._http_responses['200'] = custom_handler
        
        result, status_code = base_response.handle_response(200, {})
        
        self.assertEqual(result, {'custom': 'response'})
        self.assertEqual(status_code, 201)
        custom_handler.assert_called_once_with({}, 200)

    def test_default_response(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        mock_response = {'key': 'value'}
        result, status_code = base_response._default_response(mock_response)
        
        self.assertEqual(result, mock_response)
        self.assertEqual(status_code, 200)

    def test_default_response_custom_status(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        mock_response = {'key': 'value'}
        result, status_code = base_response._default_response(mock_response, 201)
        
        self.assertEqual(result, mock_response)
        self.assertEqual(status_code, 201)

    def test_translate(self):
        allowed_responses = [200, 400]
        base_response = BaseResponse(allowed_responses=allowed_responses)
        
        translation = {'field1': 'Value: {0}', 'field2': 'Another value: {0}'}
        base_response._translate('field1', translation, 'test')
        
        self.assertEqual(translation['field1'], 'Value: test')
        self.assertEqual(translation['field2'], 'Another value: {0}')

if __name__ == '__main__':
    unittest.main()