import os
import yaml
import typing
import logging

class Config(object):
    """Config
    """

    _CONFIG: typing.Optional[dict] = None

    def set_config_headers_scan_with(self, config_values: dict, env):
        try:
            if env.get("MENLO_MD_HEADERS_SCAN_WITH"):
                config_values['headers_scan_with'] = env.get("MENLO_MD_HEADERS_SCAN_WITH")
        except Exception as e:
            logging.warning(f"Error configuring headers_scan_with: {e}")
            # Ensure headers_scan_with has a default value if configuration fails
            if 'headers_scan_with' not in config_values:
                config_values['headers_scan_with'] = ""

    def set_config_logging(self, config_values: dict, env):
        config_values['logging']['kafka']['enabled'] = bool(env.get("MENLO_MD_KAFKA_ENABLED", config_values['logging']['kafka']['enabled']))
        config_values['logging']['kafka']['client_id'] = env.get("MENLO_MD_KAFKA_CLIENT_ID", config_values['logging']['kafka']['client_id'])
        config_values['logging']['kafka']['server'] = env.get("MENLO_MD_KAFKA_SERVER", config_values['logging']['kafka']['server'])
        config_values['logging']['kafka']['topic'] = env.get("MENLO_MD_KAFKA_TOPIC", config_values['logging']['kafka']['topic'])
        config_values['logging']['kafka']['ssl'] = bool(env.get("MENLO_MD_KAFKA_SSL", config_values['logging']['kafka']['ssl']))
        config_values['logging']['sns']['enabled'] = env.get('MENLO_MD_SNS_ENABLED', config_values['logging']['sns']['enabled'])
        config_values['logging']['sns']['arn'] = env.get('MENLO_MD_SNS_ARN', config_values['logging']['sns']['arn'])
        config_values['logging']['sns']['region'] = env.get('MENLO_MD_SNS_REGION', config_values['logging']['sns']['region'])

    def set_config_serverurl(self, config_values: dict, env):
        if env.get("MENLO_MD_URL", env.get("MDCLOUD_URL")):
            config_values['serverUrl'] = env.get("MENLO_MD_URL", env.get("MDCLOUD_URL"))
        else:
            try:
                api_type = config_values['api']['type']
                config_values['serverUrl'] = config_values['api']['url'][api_type]
            except Exception:
                config_values['serverUrl'] = "http://localhost:8008"

    def set_config_apikey(self, config_values: dict, env):
        if env.get('MENLO_MD_APIKEY'):
            config_values['apikey'] = env.get('MENLO_MD_APIKEY')
        else:
            try:
                config_values['apikey'] = config_values['api']['params']['apikey']
            except Exception:
                config_values['apikey'] = None

    def set_config_attributes(self, config_values: dict, env):
        config_values['env'] = env.get("MENLO_MD_ENV", env.get("ENVIRONMENT",'local'))
        config_values['region'] = env.get("MENLO_MD_AWS_REGION", env.get("AWS_REGION", "us-west-2"))
        config_values['commitHash'] = env.get("MENLO_MD_BITBUCKET_COMMIT_HASH", env.get("BITBUCKET_COMMIT_HASH", "-"))
        config_values['scanRule'] = env.get("MENLO_MD_MDCLOUD_RULE", env.get("MDCLOUD_RULE", "multiscan, sanitize, unarchive" if config_values['api']['type'] == "cloud" else None))
        
        self.set_config_apikey(config_values, env)

        self.set_config_serverurl(config_values, env)
        
        if env.get("MENLO_MD_SENTRY_DSN", env.get("SENTRY_DSN")):
            config_values['sentryDsn'] = env.get("MENLO_MD_SENTRY_DSN", env.get("SENTRY_DSN"))

        self.set_config_logging(config_values, env)

        if env.get("MENLO_MD_FALLBACK_TO_ORIGINAL"):
            config_values['fallbackToOriginal'] = env.get("MENLO_MD_FALLBACK_TO_ORIGINAL") == "true"

        # Handle headers_scan_with configuration
        self.set_config_headers_scan_with(config_values, env)

    def __init__(self, config_file = None):
        if config_file is None:
            raise ValueError("Please set the 'config_file' argument")
        assert os.path.exists(config_file)

        with open(config_file, 'r', encoding='utf-8') as file_data:
            Config._CONFIG = yaml.safe_load(file_data)

        self.set_config_attributes(Config._CONFIG, os.environ)

    @staticmethod
    def get_all():
        return Config._CONFIG