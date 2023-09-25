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

        Config._CONFIG['env'] = os.environ.get("MENLO_MD_ENV", os.environ.get("MENLO_MD_ENV",'local'))
        
        Config._CONFIG['region'] = os.environ.get("MENLO_MD_AWS_REGION", os.environ.get("AWS_REGION", "us-west-2"))
        
        Config._CONFIG['commitHash'] = os.environ.get("MENLO_MD_BITBUCKET_COMMIT_HASH", os.environ.get("BITBUCKET_COMMIT_HASH", "-"))
        
        Config._CONFIG['scanRule'] = os.environ.get("MENLO_MD_MDCLOUD_RULE", os.environ.get("MDCLOUD_RULE", "multiscan, sanitize, unarchive"))
        
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
            Config._CONFIG['sentryDns'] = os.environ.get("MENLO_MD_SENTRY_DSN", os.environ.get("SENTRY_DSN"))

        

    @staticmethod
    def get_all():
        return Config._CONFIG

    @staticmethod
    def get(path):
        return Config._CONFIG[path] if path in Config._CONFIG else None
        
