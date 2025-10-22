import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.utils.domain_allowlist import DomainAllowlistUtils


class TestDomainAllowlistUtils(unittest.TestCase):

    def setUp(self):
        self.config_enabled = {
            'allowlist': {
                'enabled': True,
                'aws_profile': 'test-profile',
                'db_table_name': 'test-table'
            }
        }
        self.config_disabled = {
            'allowlist': {
                'enabled': False
            }
        }

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_init_enabled(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
        
        self.assertEqual(utils.config, self.config_enabled)
        self.assertEqual(utils.domains_cache, {})
        self.assertTrue(utils.enabled)
        self.assertEqual(utils.dynamodb, mock_dynamodb)
        self.assertEqual(utils.table, mock_table)

    def test_init_disabled(self):
        utils = DomainAllowlistUtils(self.config_disabled)
        
        self.assertEqual(utils.config, self.config_disabled)
        self.assertEqual(utils.domains_cache, {})
        self.assertFalse(utils.enabled)
        self.assertFalse(hasattr(utils, 'dynamodb'))
        self.assertFalse(hasattr(utils, 'table'))

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_init_aws_exception(self, mock_boto3):
        mock_boto3.Session.side_effect = Exception("AWS Error")
        
        utils = DomainAllowlistUtils(self.config_enabled)
        
        self.assertFalse(utils.enabled)
        self.assertIsNone(utils.dynamodb)
        self.assertIsNone(utils.table)

    def test_extract_domain_scenarios(self):
        utils = DomainAllowlistUtils(self.config_disabled)
        
        test_cases = [
            ('https://example.com/path', 'example.com'),
            ('https://subdomain.example.com/path', 'example.com'),
            ('https://www.example.co.uk/path', 'co.uk'),
            ('https://test.subdomain.example.org/path', 'example.org'),
            ('http://localhost:8080/path', 'localhost'),
            ('ftp://files.example.net', 'example.net'),
            ('invalid-url', 'invalid-url'),
            ('', ''),
            ('https://', 'https://'),
        ]
        
        for input_url, expected_domain in test_cases:
            with self.subTest(input_url=input_url):
                result = utils.extract_domain(input_url)
                self.assertEqual(result, expected_domain)

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_add_to_allowlist_scenarios(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
        utils.get_cached_domains = Mock(return_value=['example.com', 'test.org'])
        
        test_cases = [
            (200, 'test-uuid', 'https://example.com/file.pdf', 'file.pdf', 'test-key', True),
            (200, 'test-uuid', 'https://other.com/file.pdf', 'file.pdf', 'test-key', False),
            (404, 'test-uuid', 'https://example.com/file.pdf', 'file.pdf', 'test-key', False),
            (200, '', 'https://example.com/file.pdf', 'file.pdf', 'test-key', False),
            (200, None, 'https://example.com/file.pdf', 'file.pdf', 'test-key', False),
        ]
        
        for http_status, uuid, srcuri, filename, apikey, should_call_put_item in test_cases:
            with self.subTest(http_status=http_status, uuid=uuid, srcuri=srcuri):
                mock_table.put_item.reset_mock()
                utils.add_to_allowlist(http_status, uuid, srcuri, filename, apikey)
                if should_call_put_item:
                    mock_table.put_item.assert_called_once_with(
                        Item={'id': f'ALLOW#{uuid}', 'filename': filename}
                    )
                else:
                    mock_table.put_item.assert_not_called()

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_get_cached_domains_disabled(self, mock_boto3):
        utils = DomainAllowlistUtils(self.config_disabled)
        result = utils.get_cached_domains('test-key')
        self.assertEqual(result, [])

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_get_cached_domains_cached(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
        
        cached_domains = ['example.com', 'test.org']
        utils.domains_cache['test-key'] = cached_domains
        
        result = utils.get_cached_domains('test-key')
        self.assertEqual(result, cached_domains)

        mock_table.get_item.assert_not_called()

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_domain_normalization_in_cache(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
    
        mock_table.get_item.return_value = {
            'Item': {
                'domains': [
                    'https://example.com',
                    'https://subdomain.test.org',
                    'http://www.demo.net',
                    'ftp://files.example.co.uk'
                ]
            }
        }
        
        result = utils.get_cached_domains('test-key')
        expected_domains = ['example.com', 'test.org', 'demo.net', 'co.uk']
        self.assertEqual(set(result), set(expected_domains))

    def test_config_without_aws_profile(self):
        config_no_profile = {
            'allowlist': {
                'enabled': True,
                'db_table_name': 'test-table'
            }
        }
        
        with patch('metadefender_menlo.api.utils.domain_allowlist.boto3') as mock_boto3:
            mock_session = Mock()
            mock_dynamodb = Mock()
            mock_table = Mock()
            
            mock_boto3.Session.return_value = mock_session
            mock_session.resource.return_value = mock_dynamodb
            mock_dynamodb.Table.return_value = mock_table
            
            utils = DomainAllowlistUtils(config_no_profile)
            
            # Should use default profile
            mock_boto3.Session.assert_called_once_with(profile_name='default')
            self.assertTrue(utils.enabled)

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_get_cached_domains_scenarios(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        utils = DomainAllowlistUtils(self.config_enabled)
        
        test_cases = [
            ('key1', {'Item': {'domains': ['https://example.com', 'https://sub.test.org']}}, ['example.com', 'test.org']),
            ('key2', {'Item': {'domains': []}}, []),
            ('key3', {}, []),
            ('key4', {'Item': {}}, []),
        ]
        
        for api_key, table_response, expected_domains in test_cases:
            with self.subTest(api_key=api_key):
                mock_table.get_item.return_value = table_response
                utils.domains_cache = {}
                
                result = utils.get_cached_domains(api_key)
                self.assertEqual(set(result), set(expected_domains))
                self.assertEqual(set(utils.domains_cache[api_key]), set(expected_domains))

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_is_in_allowlist_found_and_deleted(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
        
        test_uuid = 'test-uuid-123'
        test_filename = 'document.pdf'
        mock_table.get_item.return_value = {
            'Item': {
                'id': f'ALLOW#{test_uuid}',
                'filename': test_filename
            }
        }
        
        result, status_code = utils.is_in_allowlist(test_uuid)
        expected_response = {
            'result': 'completed',
            'outcome': 'clean',
            'report_url': '',
            'filename': test_filename,
            'modifications': ['Domain whitelisted']
        }
        self.assertEqual(result, expected_response)
        self.assertEqual(status_code, 200)
        
        mock_table.get_item.assert_called_once_with(Key={'id': f'ALLOW#{test_uuid}'})
        mock_table.delete_item.assert_called_once_with(Key={'id': f'ALLOW#{test_uuid}'})

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_is_in_allowlist_not_found(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
        
        test_uuid = 'test-uuid-456'
        mock_table.get_item.return_value = {}
        
        result, status_code = utils.is_in_allowlist(test_uuid)
        
        self.assertIsNone(result)
        self.assertIsNone(status_code)
        
        mock_table.get_item.assert_called_once_with(Key={'id': f'ALLOW#{test_uuid}'})
        mock_table.delete_item.assert_not_called()

    @patch('metadefender_menlo.api.utils.domain_allowlist.boto3')
    def test_is_in_allowlist_empty_item(self, mock_boto3):
        mock_session = Mock()
        mock_dynamodb = Mock()
        mock_table = Mock()
        
        mock_boto3.Session.return_value = mock_session
        mock_session.resource.return_value = mock_dynamodb
        mock_dynamodb.Table.return_value = mock_table
        
        utils = DomainAllowlistUtils(self.config_enabled)
    
        test_uuid = 'test-uuid-789'
        mock_table.get_item.return_value = {
            'Item': {
                'id': f'ALLOW#{test_uuid}'
            }
        }
        
        result, status_code = utils.is_in_allowlist(test_uuid)
        
        expected_response = {
            'result': 'completed',
            'outcome': 'clean',
            'report_url': '',
            'filename': '',
            'modifications': ['Domain whitelisted']
        }
        self.assertEqual(result, expected_response)
        self.assertEqual(status_code, 200)
        
        mock_table.get_item.assert_called_once_with(Key={'id': f'ALLOW#{test_uuid}'})
        mock_table.delete_item.assert_called_once_with(Key={'id': f'ALLOW#{test_uuid}'})

    def test_is_in_allowlist_disabled(self):
        utils = DomainAllowlistUtils(self.config_disabled)
        
        with self.assertRaises(AttributeError):
            utils.is_in_allowlist('test-uuid')

if __name__ == '__main__':
    unittest.main()
