import unittest
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.utils.http_client_manager import HttpClientManager


class TestHttpClientManager(unittest.TestCase):

    def setUp(self):
        HttpClientManager._client = None
        HttpClientManager._limits = None

    def test_class_variables_initial_state(self):
        self.assertIsNone(HttpClientManager._client)
        self.assertIsNone(HttpClientManager._limits)

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.Limits')
    def test_build_limits_scenarios(self, mock_limits_class, mock_config_get_all):
        mock_limits_instance = Mock()
        mock_limits_class.return_value = mock_limits_instance
        
        test_cases = [
            ({}, 1),
            ({'httpx_limits': {}}, 1),
            ({'httpx_limits': {'enabled': False}}, 1),
            ({'httpx_limits': {'enabled': True}}, 1),
            ({'httpx_limits': {'enabled': True, 'max_connections': 100}}, 1),
            ({'httpx_limits': {'enabled': True, 'max_connections': 'invalid'}}, 1),
            ({'httpx_limits': {'enabled': True, 'max_connections': None}}, 1),
        ]
        
        for config_data, expected_calls in test_cases:
            with self.subTest(config_data=config_data):
                mock_config_get_all.return_value = config_data
                mock_limits_class.reset_mock()
                
                result = HttpClientManager._build_limits()
                
                self.assertEqual(result, mock_limits_instance)
                self.assertEqual(mock_limits_class.call_count, expected_calls)

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.Limits')
    def test_build_limits_with_valid_max_connections(self, mock_limits_class, mock_config_get_all):
        mock_limits_instance = Mock()
        mock_limits_class.return_value = mock_limits_instance
        
        config_data = {
            'httpx_limits': {
                'enabled': True,
                'max_connections': 50
            }
        }
        mock_config_get_all.return_value = config_data
        
        result = HttpClientManager._build_limits()
        
        self.assertEqual(result, mock_limits_instance)
        mock_limits_class.assert_called_once_with(max_connections=50)

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.Limits')
    def test_build_limits_with_invalid_max_connections(self, mock_limits_class, mock_config_get_all):
        mock_limits_instance = Mock()
        mock_limits_class.return_value = mock_limits_instance
        
        config_data = {
            'httpx_limits': {
                'enabled': True,
                'max_connections': 'not_a_number'
            }
        }
        mock_config_get_all.return_value = config_data
        
        result = HttpClientManager._build_limits()
        
        self.assertEqual(result, mock_limits_instance)
        mock_limits_class.assert_called_once_with()

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.Limits')
    def test_build_limits_with_none_max_connections(self, mock_limits_class, mock_config_get_all):
        mock_limits_instance = Mock()
        mock_limits_class.return_value = mock_limits_instance
        
        config_data = {
            'httpx_limits': {
                'enabled': True,
                'max_connections': None
            }
        }
        mock_config_get_all.return_value = config_data
        
        result = HttpClientManager._build_limits()
        
        self.assertEqual(result, mock_limits_instance)
        mock_limits_class.assert_called_once_with()

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.AsyncClient')
    def test_get_client_scenarios(self, mock_async_client_class, mock_config_get_all):
        mock_client_instance = Mock()
        mock_async_client_class.return_value = mock_client_instance
        mock_config_get_all.return_value = {}
        
        result1 = HttpClientManager.get_client()
        result2 = HttpClientManager.get_client()
        
        self.assertEqual(result1, result2)
        self.assertEqual(result1, mock_client_instance)
        self.assertEqual(HttpClientManager._client, mock_client_instance)
        self.assertIsNotNone(HttpClientManager._limits)
        self.assertEqual(mock_async_client_class.call_count, 1)

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    @patch('metadefender_menlo.api.utils.http_client_manager.httpx.AsyncClient')
    def test_get_client_with_existing_limits(self, mock_async_client_class, mock_config_get_all):
        mock_client_instance = Mock()
        mock_async_client_class.return_value = mock_client_instance
        
        HttpClientManager._limits = Mock()
        
        result = HttpClientManager.get_client()
        
        self.assertEqual(result, mock_client_instance)
        mock_async_client_class.assert_called_once_with(limits=HttpClientManager._limits)

    def test_close_client_scenarios(self):
        mock_client = Mock()
        mock_client.aclose = AsyncMock()
        HttpClientManager._client = mock_client
        
        asyncio.run(HttpClientManager.close_client())
        
        mock_client.aclose.assert_called_once()
        self.assertIsNone(HttpClientManager._client)

        HttpClientManager._client = None
        asyncio.run(HttpClientManager.close_client())
        self.assertIsNone(HttpClientManager._client)

    @patch('metadefender_menlo.api.utils.http_client_manager.Config.get_all')
    def test_build_limits_config_edge_cases(self, mock_config_get_all):
        with patch('metadefender_menlo.api.utils.http_client_manager.httpx.Limits') as mock_limits_class:
            mock_limits_instance = Mock()
            mock_limits_class.return_value = mock_limits_instance
            
            test_cases = [
                None,
                {'httpx_limits': {}},
                {'httpx_limits': None}
            ]
            
            for config_data in test_cases:
                with self.subTest(config_data=config_data):
                    mock_config_get_all.return_value = config_data
                    mock_limits_class.reset_mock()
                    
                    result = HttpClientManager._build_limits()
                    
                    self.assertEqual(result, mock_limits_instance)
                    mock_limits_class.assert_called_once_with()

    def test_class_variables_reset_after_close(self):
        HttpClientManager._client = Mock()
        HttpClientManager._limits = Mock()
        
        HttpClientManager._client = None
        HttpClientManager._limits = None
        
        self.assertIsNone(HttpClientManager._client)
        self.assertIsNone(HttpClientManager._limits)


if __name__ == '__main__':
    unittest.main()
