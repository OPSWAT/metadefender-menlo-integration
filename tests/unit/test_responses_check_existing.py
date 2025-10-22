import unittest
from unittest.mock import patch, AsyncMock

import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.responses.check_existing import CheckExisting


class TestCheckExisting(unittest.IsolatedAsyncioTestCase):
    """Simple test suite for CheckExisting class with 90%+ coverage"""

    def setUp(self):
        """Reset class variables before each test"""
        CheckExisting._allowed_responses = []
        CheckExisting._http_responses = {}

    def test_init(self):
        """Test initialization - covers lines 9-15"""
        check_existing = CheckExisting(apikey='test_key')
        
        self.assertEqual(check_existing._allowed_responses, [200, 400, 401, 404, 500])
        self.assertEqual(check_existing._apikey, 'test_key')
        self.assertEqual(len(check_existing._http_responses), 5)  # 200, 400, 401, 404, 500
        self.assertIn('200', check_existing._http_responses)
        self.assertIn('400', check_existing._http_responses)
        self.assertIn('401', check_existing._http_responses)
        self.assertIn('404', check_existing._http_responses)
        self.assertIn('500', check_existing._http_responses)

    def test_init_default_apikey(self):
        """Test initialization with default apikey - covers lines 9-15"""
        check_existing = CheckExisting()
        
        self.assertEqual(check_existing._apikey, '')

    async def test_response200_with_data_id(self):
        """Test response200 with data_id - covers lines 17-28"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing._CheckExisting__response200({'data_id': 'test_id'}, 200)
        
        self.assertEqual(result, {'uuid': 'test_id', 'result': 'found'})
        self.assertEqual(status_code, 200)

    async def test_response200_without_data_id(self):
        """Test response200 without data_id - covers lines 29-30"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing._CheckExisting__response200({}, 200)
        
        self.assertEqual(result, {})
        self.assertEqual(status_code, 404)

    async def test_response200_with_none_response(self):
        """Test response200 with None response - covers lines 31-35"""
        check_existing = CheckExisting()
        
        with patch('metadefender_menlo.api.responses.check_existing.logging.error') as mock_logging:
            result, status_code = await check_existing._CheckExisting__response200(None, 200)
            
            self.assertEqual(result, {})
            self.assertEqual(status_code, 500)
            mock_logging.assert_called_once()

    async def test_response200_with_invalid_response(self):
        """Test response200 with invalid response - covers lines 29-30"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing._CheckExisting__response200('invalid', 200)
        
        # When response is invalid (no 'data_id' key), it returns the original response with 404
        self.assertEqual(result, 'invalid')
        self.assertEqual(status_code, 404)

    async def test_response200_with_exception(self):
        """Test response200 with exception - covers lines 31-35"""
        check_existing = CheckExisting()
        
        # Mock _translate to raise an exception
        with patch.object(check_existing, '_translate', side_effect=Exception('Test error')):
            with patch('metadefender_menlo.api.responses.check_existing.logging.error') as mock_logging:
                result, status_code = await check_existing._CheckExisting__response200({'data_id': 'test'}, 200)
                
                self.assertEqual(result, {})
                self.assertEqual(status_code, 500)
                mock_logging.assert_called_once()

    async def test_response400(self):
        """Test response400 - covers lines 37-41"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing._CheckExisting__response400({'sha256': 'test_hash'}, 400)
        
        self.assertEqual(result, {'uuid': 'test_hash', 'result': '404'})
        self.assertEqual(status_code, 200)

    async def test_response401(self):
        """Test response401 - covers lines 43-44"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing._CheckExisting__response401({}, 401)
        
        self.assertEqual(result, {})
        self.assertEqual(status_code, 401)

    async def test_handle_response_success(self):
        """Test handle_response with success - covers BaseResponse integration"""
        check_existing = CheckExisting()
        
        result, status_code = await check_existing.handle_response({'data_id': 'test_id'}, 200)
        
        self.assertEqual(result, {'uuid': 'test_id', 'result': 'found'})
        self.assertEqual(status_code, 200)

    async def test_handle_response_not_allowed(self):
        """Test handle_response with not allowed status - covers BaseResponse integration"""
        check_existing = CheckExisting()
        
        with self.assertRaises(ValueError):
            await check_existing.handle_response({}, 999)


if __name__ == '__main__':
    unittest.main()