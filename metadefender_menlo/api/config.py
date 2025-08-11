import os
import yaml
import typing

class Config(object):
    """Config
    """

    _CONFIG: typing.Optional[dict] = None

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
            except Exception as error:
                Config._CONFIG['apikey'] = None
        
        if os.environ.get("MDCLOUD_URL", os.environ.get("MENLO_MD_URL")):
            Config._CONFIG['serverUrl'] = os.environ.get("MENLO_MD_URL", os.environ.get("MDCLOUD_URL"))
        else:
            try:
                api_type = Config._CONFIG["api"]["type"]
                Config._CONFIG['serverUrl'] = Config._CONFIG["api"]["url"][api_type]
            except Exception as error:
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

        # Handle scanWith configuration
        try:
            if os.environ.get("MENLO_MD_SCAN_WITH_ENABLED"):
                # Initialize scanWith as dict if it doesn't exist
                if 'scanWith' not in Config._CONFIG:
                    Config._CONFIG['scanWith'] = {}
                elif isinstance(Config._CONFIG['scanWith'], str):
                    # Convert old string format to new dict format
                    Config._CONFIG['scanWith'] = {'enabled': True}
                
                Config._CONFIG['scanWith']['enabled'] = os.environ.get("MENLO_MD_SCAN_WITH_ENABLED") == "true"
            
            # Backward compatibility: if MENLO_MD_SCAN_WITH is set, enable it
            if os.environ.get("MENLO_MD_SCAN_WITH"):
                if 'scanWith' not in Config._CONFIG:
                    Config._CONFIG['scanWith'] = {}
                elif isinstance(Config._CONFIG['scanWith'], str):
                    Config._CONFIG['scanWith'] = {'enabled': True}
                
                Config._CONFIG['scanWith']['enabled'] = True
        except Exception as e:
            logging.warning(f"Error configuring scanWith: {e}")
            # Ensure scanWith has a default value if configuration fails
            if 'scanWith' not in Config._CONFIG:
                Config._CONFIG['scanWith'] = {'enabled': False}

        

    @staticmethod
    def get_all():
        return Config._CONFIG

    @staticmethod
    def get(path):
        return Config._CONFIG[path] if path in Config._CONFIG else None
        
