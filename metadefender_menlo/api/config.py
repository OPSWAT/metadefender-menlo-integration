import os
import yaml
import typing

class Config(object):
    """Config Singleton
    """

    _CONFIG: typing.Optional[dict] = None

    def __init__(self, config_file = None):
        if config_file is None:
            raise Exception("Please set the 'config_file' argument")
        assert os.path.exists(config_file)

        with open(config_file, 'r', encoding='utf-8') as file_data:
            Config._CONFIG = yaml.safe_load(file_data)

    @staticmethod
    def get_all():
        return Config._CONFIG

    @staticmethod
    def get(path):
        return Config._CONFIG[path] if path in Config._CONFIG else None
        
