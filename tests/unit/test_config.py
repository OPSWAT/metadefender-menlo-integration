import unittest
import os
import tempfile
import yaml
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.config import Config


class TestConfig(unittest.TestCase):
   
    def setUp(self):
        Config._CONFIG = None
        self.test_config = {
            'api': {
                'type': 'cloud',
                'params': {
                    'apikey': 'test-apikey-from-file'
                },
                'url': {
                    'core': 'https://core.test.com',
                    'cloud': 'https://cloud.test.com'
                }
            },
            'logging': {
                'kafka': {
                    'enabled': True,
                    'client_id': 'test-client',
                    'server': 'kafka.test.com',
                    'topic': 'test-topic',
                    'ssl': False
                },
                'sns': {
                    'enabled': False,
                    'arn': 'arn:aws:sns:us-west-2:123456789012:test-topic',
                    'region': 'us-west-2'
                }
            },
            'fallbackToOriginal': True,
            'headers_scan_with': 'test-headers'
        }
        
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(self.test_config, self.temp_file)
        self.temp_file.close()
        
        self.env_vars_to_clear = [
            'MENLO_MD_ENV', 'ENVIRONMENT',
            'MENLO_MD_AWS_REGION', 'AWS_REGION',
            'MENLO_MD_BITBUCKET_COMMIT_HASH', 'BITBUCKET_COMMIT_HASH',
            'MENLO_MD_MDCLOUD_RULE', 'MDCLOUD_RULE',
            'MENLO_MD_APIKEY',
            'MENLO_MD_URL', 'MDCLOUD_URL',
            'MENLO_MD_SENTRY_DSN', 'SENTRY_DSN',
            'MENLO_MD_KAFKA_ENABLED', 'MENLO_MD_KAFKA_CLIENT_ID',
            'MENLO_MD_KAFKA_SERVER', 'MENLO_MD_KAFKA_TOPIC', 'MENLO_MD_KAFKA_SSL',
            'MENLO_MD_SNS_ENABLED', 'MENLO_MD_SNS_ARN', 'MENLO_MD_SNS_REGION',
            'MENLO_MD_FALLBACK_TO_ORIGINAL',
            'MENLO_MD_HEADERS_SCAN_WITH'
        ]
        
        self.original_env_vars = {}
        for var in self.env_vars_to_clear:
            self.original_env_vars[var] = os.environ.get(var)
            if var in os.environ:
                del os.environ[var]

    def cleanUp(self):
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        for var, value in self.original_env_vars.items():
            if value is not None:
                os.environ[var] = value
            elif var in os.environ:
                del os.environ[var]
        Config._CONFIG = None

    def test_constructor_validations(self):
        config = Config(self.temp_file.name)
        self.assertIsNotNone(Config._CONFIG)
        self.assertEqual(Config._CONFIG['api']['type'], 'cloud')
        self.assertEqual(Config._CONFIG['api']['params']['apikey'], 'test-apikey-from-file')
        self.assertEqual(Config._CONFIG['logging']['kafka']['enabled'], True)

        Config._CONFIG = None
        with self.assertRaises(Exception) as context:
            Config(None)
        self.assertEqual(str(context.exception), "Please set the 'config_file' argument")
        self.assertIsNone(Config._CONFIG)

        with self.assertRaises(AssertionError):
            Config('/nonexistent/file.yml')
        self.assertIsNone(Config._CONFIG)

        invalid_yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        invalid_yaml_file.write('invalid: yaml: content: [')
        invalid_yaml_file.close()
        
        try:
            with self.assertRaises(yaml.YAMLError):
                Config(invalid_yaml_file.name)
            self.assertIsNone(Config._CONFIG)
        finally:
            os.unlink(invalid_yaml_file.name)

    def test_environment_variable_precedence(self):
        os.environ['MENLO_MD_ENV'] = 'production'
        os.environ['ENVIRONMENT'] = 'staging'
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['env'], 'production')

        del os.environ['MENLO_MD_ENV']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['env'], 'staging')
        
        del os.environ['ENVIRONMENT']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['env'], 'local')

        os.environ['MENLO_MD_AWS_REGION'] = 'us-east-1'
        os.environ['AWS_REGION'] = 'eu-west-1'
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['region'], 'us-east-1')
        
        del os.environ['MENLO_MD_AWS_REGION']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['region'], 'eu-west-1')
        
        del os.environ['AWS_REGION']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['region'], 'us-west-2')

        os.environ['MENLO_MD_BITBUCKET_COMMIT_HASH'] = 'abc123-menlo'
        os.environ['BITBUCKET_COMMIT_HASH'] = 'def456-bitbucket'
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['commitHash'], 'abc123-menlo')
        
        del os.environ['MENLO_MD_BITBUCKET_COMMIT_HASH']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['commitHash'], 'def456-bitbucket')
        
        del os.environ['BITBUCKET_COMMIT_HASH']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['commitHash'], '-')

    def test_scan_rule_configuration(self):
        os.environ['MENLO_MD_MDCLOUD_RULE'] = 'custom-scan-rule'
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['scanRule'], 'custom-scan-rule')
        
        del os.environ['MENLO_MD_MDCLOUD_RULE']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['scanRule'], 'multiscan, sanitize, unarchive')

        core_config = self.test_config.copy()
        core_config['api']['type'] = 'core'
        core_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(core_config, core_file)
        core_file.close()
        
        try:
            Config._CONFIG = None
            config = Config(core_file.name)
            self.assertIsNone(Config._CONFIG['scanRule'])
            Config._CONFIG = None
            os.environ['MENLO_MD_MDCLOUD_RULE'] = 'core-custom-rule'
            config = Config(core_file.name)
            self.assertEqual(Config._CONFIG['scanRule'], 'core-custom-rule')
        finally:
            os.unlink(core_file.name)

    def test_apikey_configuration(self):
        os.environ['MENLO_MD_APIKEY'] = 'env-apikey-123'
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['apikey'], 'env-apikey-123')
        
        del os.environ['MENLO_MD_APIKEY']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['apikey'], 'test-apikey-from-file')

        no_apikey_config = self.test_config.copy()
        del no_apikey_config['api']['params']['apikey']
        no_apikey_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(no_apikey_config, no_apikey_file)
        no_apikey_file.close()
        
        try:
            Config._CONFIG = None
            config = Config(no_apikey_file.name)
            self.assertIsNone(Config._CONFIG['apikey'])
        finally:
            os.unlink(no_apikey_file.name)

    def test_server_url_configuration(self):
        os.environ['MENLO_MD_URL'] = 'https://menlo-custom.com'
        os.environ['MDCLOUD_URL'] = 'https://mdcloud-custom.com'
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['serverUrl'], 'https://menlo-custom.com')

        del os.environ['MENLO_MD_URL']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['serverUrl'], 'https://mdcloud-custom.com')
        
        del os.environ['MDCLOUD_URL']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['serverUrl'], 'https://cloud.test.com')

        core_config = self.test_config.copy()
        core_config['api']['type'] = 'core'
        core_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(core_config, core_file)
        core_file.close()
        
        try:
            Config._CONFIG = None
            config = Config(core_file.name)
            self.assertEqual(Config._CONFIG['serverUrl'], 'https://core.test.com')
            Config._CONFIG = None
            os.environ['MENLO_MD_URL'] = 'https://env-override.com'
            config = Config(core_file.name)
            self.assertEqual(Config._CONFIG['serverUrl'], 'https://env-override.com')
        finally:
            os.unlink(core_file.name)

        del os.environ['MENLO_MD_URL']
        invalid_api_config = self.test_config.copy()
        del invalid_api_config['api']['url']
        invalid_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(invalid_api_config, invalid_file)
        invalid_file.close()
        
        try:
            Config._CONFIG = None
            config = Config(invalid_file.name)
            self.assertEqual(Config._CONFIG['serverUrl'], 'http://localhost:8008')
        finally:
            os.unlink(invalid_file.name)

    def test_sentry_and_logging_configuration(self):
        os.environ['MENLO_MD_SENTRY_DSN'] = 'https://menlo-sentry@sentry.io/123'
        os.environ['SENTRY_DSN'] = 'https://generic-sentry@sentry.io/456'
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['sentryDsn'], 'https://menlo-sentry@sentry.io/123')
        
        del os.environ['MENLO_MD_SENTRY_DSN']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['sentryDsn'], 'https://generic-sentry@sentry.io/456')
        
        del os.environ['SENTRY_DSN']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertNotIn('sentryDsn', Config._CONFIG)

        os.environ['MENLO_MD_SNS_ENABLED'] = 'true'
        os.environ['MENLO_MD_SNS_ARN'] = 'arn:aws:sns:us-east-1:123456789012:env-topic'
        os.environ['MENLO_MD_SNS_REGION'] = 'us-east-1'
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        
        self.assertEqual(Config._CONFIG['logging']['sns']['enabled'], 'true')
        self.assertEqual(Config._CONFIG['logging']['sns']['arn'], 'arn:aws:sns:us-east-1:123456789012:env-topic')
        self.assertEqual(Config._CONFIG['logging']['sns']['region'], 'us-east-1')
        
        Config._CONFIG = None
        del os.environ['MENLO_MD_SNS_ENABLED']
        del os.environ['MENLO_MD_SNS_ARN']
        del os.environ['MENLO_MD_SNS_REGION']
        
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['logging']['sns']['enabled'], False)
        self.assertEqual(Config._CONFIG['logging']['sns']['arn'], 'arn:aws:sns:us-west-2:123456789012:test-topic')
        self.assertEqual(Config._CONFIG['logging']['sns']['region'], 'us-west-2')

    def test_fallback_and_headers_configuration(self):
        os.environ['MENLO_MD_FALLBACK_TO_ORIGINAL'] = 'false'
        config = Config(self.temp_file.name)
        self.assertFalse(Config._CONFIG['fallbackToOriginal'])
        
        Config._CONFIG = None
        os.environ['MENLO_MD_FALLBACK_TO_ORIGINAL'] = 'true'
        config = Config(self.temp_file.name)
        self.assertTrue(Config._CONFIG['fallbackToOriginal'])
        
        del os.environ['MENLO_MD_FALLBACK_TO_ORIGINAL']
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertTrue(Config._CONFIG['fallbackToOriginal'])

        os.environ['MENLO_MD_HEADERS_SCAN_WITH'] = 'custom-headers-value'
        Config._CONFIG = None
        config = Config(self.temp_file.name)
        self.assertEqual(Config._CONFIG['headers_scan_with'], 'custom-headers-value')

    def test_get_all_method(self):
        config = Config(self.temp_file.name)
        result = Config.get_all()
        
        self.assertIsNotNone(result)
        self.assertIs(result, Config._CONFIG)
        self.assertEqual(result['api']['type'], 'cloud')
        self.assertEqual(result['logging']['kafka']['enabled'], True)
        self.assertIn('env', result)
        self.assertIn('region', result)
        self.assertIn('commitHash', result)

        Config._CONFIG = None
        result = Config.get_all()
        self.assertIsNone(result)

    def test_comprehensive_environment_override(self):
        os.environ['MENLO_MD_ENV'] = 'production'
        os.environ['MENLO_MD_AWS_REGION'] = 'us-east-1'
        os.environ['MENLO_MD_BITBUCKET_COMMIT_HASH'] = 'prod-commit-123'
        os.environ['MENLO_MD_MDCLOUD_RULE'] = 'production-scan-rule'
        os.environ['MENLO_MD_APIKEY'] = 'prod-apikey-456'
        os.environ['MENLO_MD_URL'] = 'https://prod.metadefender.com'
        os.environ['MENLO_MD_SENTRY_DSN'] = 'https://prod-sentry@sentry.io/789'
        os.environ['MENLO_MD_KAFKA_ENABLED'] = 'true'
        os.environ['MENLO_MD_KAFKA_CLIENT_ID'] = 'prod-client'
        os.environ['MENLO_MD_KAFKA_SERVER'] = 'prod-kafka.com'
        os.environ['MENLO_MD_KAFKA_TOPIC'] = 'prod-topic'
        os.environ['MENLO_MD_KAFKA_SSL'] = 'true'
        os.environ['MENLO_MD_SNS_ENABLED'] = 'true'
        os.environ['MENLO_MD_SNS_ARN'] = 'arn:aws:sns:us-east-1:123456789012:prod-topic'
        os.environ['MENLO_MD_SNS_REGION'] = 'us-east-1'
        os.environ['MENLO_MD_FALLBACK_TO_ORIGINAL'] = 'false'
        os.environ['MENLO_MD_HEADERS_SCAN_WITH'] = 'prod-headers'
        
        config = Config(self.temp_file.name)
        final_config = Config.get_all()
        
        self.assertEqual(final_config['env'], 'production')
        self.assertEqual(final_config['region'], 'us-east-1')
        self.assertEqual(final_config['commitHash'], 'prod-commit-123')
        self.assertEqual(final_config['scanRule'], 'production-scan-rule')
        self.assertEqual(final_config['apikey'], 'prod-apikey-456')
        self.assertEqual(final_config['serverUrl'], 'https://prod.metadefender.com')
        self.assertEqual(final_config['sentryDsn'], 'https://prod-sentry@sentry.io/789')
        self.assertTrue(final_config['logging']['kafka']['enabled'])
        self.assertEqual(final_config['logging']['kafka']['client_id'], 'prod-client')
        self.assertEqual(final_config['logging']['kafka']['server'], 'prod-kafka.com')
        self.assertEqual(final_config['logging']['kafka']['topic'], 'prod-topic')
        self.assertTrue(final_config['logging']['kafka']['ssl'])
        self.assertEqual(final_config['logging']['sns']['enabled'], 'true')
        self.assertEqual(final_config['logging']['sns']['arn'], 'arn:aws:sns:us-east-1:123456789012:prod-topic')
        self.assertEqual(final_config['logging']['sns']['region'], 'us-east-1')
        self.assertFalse(final_config['fallbackToOriginal'])
        self.assertEqual(final_config['headers_scan_with'], 'prod-headers')


if __name__ == '__main__':
    unittest.main()
