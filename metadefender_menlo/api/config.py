import os
import yaml
import typing
import boto3
import logging

class Config(object):
    """Config
    """

    _CONFIG: typing.Optional[dict] = None
    _domains_cache: dict = {}
    _dynamodb = None
    _table = None
    _submit_endpoint_timeout = None
    _result_endpoint_timeout = None
    _sanitized_file_endpoint_timeout = None
    _check_endpoint_timeout = None

    def __init__(self, config_file = None):
        if config_file is None:
            raise Exception("Please set the 'config_file' argument")
        assert os.path.exists(config_file)

        with open(config_file, 'r', encoding='utf-8') as file_data:
            Config._CONFIG = yaml.safe_load(file_data)

        Config._CONFIG['env'] = os.environ.get("MENLO_MD_ENV", os.environ.get("ENVIRONMENT",'local'))
        
        Config._CONFIG['region'] = os.environ.get("MENLO_MD_AWS_REGION", os.environ.get("AWS_REGION", "us-west-2"))
        
        Config._CONFIG['commitHash'] = os.environ.get("MENLO_MD_BITBUCKET_COMMIT_HASH", os.environ.get("BITBUCKET_COMMIT_HASH", "-"))
        
        Config._CONFIG['scanRule'] = os.environ.get("MENLO_MD_MDCLOUD_RULE", os.environ.get("MDCLOUD_RULE", "multiscan, sanitize, unarchive" if Config._CONFIG['api']['type'] == "cloud" else None)) 

        if os.environ.get('MENLO_MD_APIKEY'):
            Config._CONFIG['apikey'] = os.environ.get('MENLO_MD_APIKEY')
        else:
            try:
                Config._CONFIG['apikey'] = Config._CONFIG['api']["params"]["apikey"]
            except Exception:
                Config._CONFIG['apikey'] = None
        
        if os.environ.get("MDCLOUD_URL", os.environ.get("MENLO_MD_URL")):
            Config._CONFIG['serverUrl'] = os.environ.get("MENLO_MD_URL", os.environ.get("MDCLOUD_URL"))
        else:
            try:
                api_type = Config._CONFIG["api"]["type"]
                Config._CONFIG['serverUrl'] = Config._CONFIG["api"]["url"][api_type]
            except Exception:
                Config._CONFIG['serverUrl'] = "http://localhost:8008"
        
        if os.environ.get("MENLO_MD_SENTRY_DSN", os.environ.get("SENTRY_DSN")):
            Config._CONFIG['sentryDsn'] = os.environ.get("MENLO_MD_SENTRY_DSN", os.environ.get("SENTRY_DSN"))

        Config._CONFIG['logging']['kafka']['enabled'] = bool(os.environ.get("MENLO_MD_KAFKA_ENABLED", Config._CONFIG['logging']['kafka']['enabled']))
        Config._CONFIG['logging']['kafka']['client_id'] = os.environ.get("MENLO_MD_KAFKA_CLIENT_ID", Config._CONFIG['logging']['kafka']['client_id'])
        Config._CONFIG['logging']['kafka']['server'] = os.environ.get("MENLO_MD_KAFKA_SERVER", Config._CONFIG['logging']['kafka']['server'])
        Config._CONFIG['logging']['kafka']['topic'] = os.environ.get("MENLO_MD_KAFKA_TOPIC", Config._CONFIG['logging']['kafka']['topic'])
        Config._CONFIG['logging']['kafka']['ssl'] = bool(os.environ.get("MENLO_MD_KAFKA_SSL", Config._CONFIG['logging']['kafka']['ssl']))

        Config._CONFIG['logging']['sns']['enabled'] = os.environ.get('MENLO_MD_SNS_ENABLED', Config._CONFIG['logging']['sns']['enabled'])
        Config._CONFIG['logging']['sns']['arn'] = os.environ.get('MENLO_MD_SNS_ARN', Config._CONFIG['logging']['sns']['arn'])
        Config._CONFIG['logging']['sns']['region'] = os.environ.get('MENLO_MD_SNS_REGION', Config._CONFIG['logging']['sns']['region'])

        if os.environ.get("MENLO_MD_FALLBACK_TO_ORIGINAL"):
            Config._CONFIG['fallbackToOriginal'] = os.environ.get("MENLO_MD_FALLBACK_TO_ORIGINAL") == "true"

        # Handle headers_scan_with configuration
        try:
            if os.environ.get("MENLO_MD_HEADERS_SCAN_WITH"):
                Config._CONFIG['headers_scan_with'] = os.environ.get("MENLO_MD_HEADERS_SCAN_WITH")
        except Exception as e:
            logging.warning(f"Error configuring headers_scan_with: {e}")
            # Ensure headers_scan_with has a default value if configuration fails
            if 'headers_scan_with' not in Config._CONFIG:
                Config._CONFIG['headers_scan_with'] = ""

        self._init_aws_resources()
        self._init_timeouts()

    
    def _init_aws_resources(self):
        if Config._CONFIG['allowlist'].get('enabled'):
            try:
                session = boto3.Session(profile_name=Config._CONFIG['allowlist'].get('aws_profile', 'default'))
                Config._dynamodb = session.resource('dynamodb')
                Config._table = Config._dynamodb.Table(Config._CONFIG['allowlist']['db_table_name'])
            except Exception:
                Config._dynamodb = None
                Config._table = None
    
    def _init_timeouts(self):
        if Config._CONFIG['timeout']['result']['enabled']:
            Config._result_endpoint_timeout = Config._CONFIG['timeout']['result']['value']

        if Config._CONFIG['timeout']['submit']['enabled']:
            Config._submit_endpoint_timeout = Config._CONFIG['timeout']['submit']['value']

        if Config._CONFIG['timeout']['sanitized']['enabled']:
            Config._sanitized_file_endpoint_timeout = Config._CONFIG['timeout']['sanitized']['value']

        if Config._CONFIG['timeout']['check']['enabled']:
            Config._check_endpoint_timeout = Config._CONFIG['timeout']['check']['value']

    @staticmethod
    def get_all():
        return Config._CONFIG

    @staticmethod
    def get(path):
        return Config._CONFIG[path] if path in Config._CONFIG else None
    
    @staticmethod
    def get_domains_cache():
        return Config._domains_cache
    
    @staticmethod
    def get_dynamodb():
        return Config._dynamodb
    
    @staticmethod
    def get_table():
        return Config._table
    
    @staticmethod
    def get_submit_endpoint_timeout():
        return Config._submit_endpoint_timeout
    
    @staticmethod
    def get_result_endpoint_timeout():
        return Config._result_endpoint_timeout
    
    @staticmethod
    def get_sanitized_file_endpoint_timeout():
        return Config._sanitized_file_endpoint_timeout
    
    @staticmethod
    def get_check_endpoint_timeout():
        return Config._check_endpoint_timeout
    
    @staticmethod
    def get_cached_domains(api_key: str) -> list:
        if not Config._dynamodb:
            return []
            
        if api_key not in Config._domains_cache:
            api_key_response = Config._table.get_item(Key={'id': f'APIKEY#{api_key}'})
            Config._domains_cache[api_key] = api_key_response.get('Item', {}).get('domains', [])
        return Config._domains_cache.get(api_key, [])
        
