
import asyncio
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from os import environ
import json
from dotenv import load_dotenv
import tornado.ioloop
import tornado.web
import sentry_sdk
from sentry_sdk.integrations.tornado import TornadoIntegration
from metadefender_menlo.api.config import Config

from metadefender_menlo.api.handlers.analysis_result import AnalysisResultHandler
from metadefender_menlo.api.handlers.check_existing import CheckExistingHandler
from metadefender_menlo.api.handlers.file_metadata import InboundMetadataHandler
from metadefender_menlo.api.handlers.file_submit import FileSubmitHandler
from metadefender_menlo.api.handlers.health_check import HealthCheckHandler
from metadefender_menlo.api.handlers.retrieve_sanitized import RetrieveSanitizedHandler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.log_handlers.kafka_log import KafkaLogHandler
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.handlers.base_handler import LogRequestFilter


SERVER_PORT = 3000
HOST = "0.0.0.0"
API_VERSION = "/api/v1"

settings = {}

CONF_FILE_PATH = os.path.dirname(os.path.abspath(__file__))
Config(CONF_FILE_PATH+'/../config.yml')


def init_sentry():
    menlo_env = environ.get("MENLO_ENV", 'local')
    if menlo_env != 'local':
        sentry_sdk.init(
            dsn=environ.get("SENTRY_DSN"),
            integrations=[
                TornadoIntegration(),
            ],
            environment=menlo_env,
            traces_sample_rate=1.0,
        )


def get_sns_config(config_path):
    sns_config_file = open(config_path, encoding="utf-8")

    sns_config = json.load(sns_config_file)
    rule = environ.get("MDCLOUD_RULE", "multiscan, sanitize, unarchive")
    if rule != "cdr":
        rule=""
    else:
        rule = "_"+rule
    environment_name = "menlo_middleware_"+environ.get("MENLO_ENV", 'dev')+rule
    sns_config_file.close()
    if environment_name in sns_config:
        connection = sns_config[environment_name]
        return {
            "arn": connection["arn"],
            "region": connection["region"]
        }
    return None


def get_kafka_config(kafka_config_path):
    kafka_config_file = open(kafka_config_path, encoding="utf-8")
    kafka_config = json.load(kafka_config_file)
    kafka_config_file.close()
    return kafka_config


def init_logging(config, sns_config_path):
    if "enabled" not in config or not config["enabled"]:
        return

    load_dotenv()
    logger = logging.getLogger()
    logging.getLogger('tornado.access').disabled = True
    logging.getLogger('kafka.conn').disabled = True
    logging.getLogger('kafka.access').disabled = True
    logger.setLevel(config["level"])
    logfile = config["logfile"]
    # create log handlers
    log_handler = TimedRotatingFileHandler(
        filename=logfile, when="h", interval=config["interval"], backupCount=config["backup_count"])

    kafka_config = get_kafka_config('./metadefender_menlo/conf/kafka-config.json')
    log_handler_kafka = KafkaLogHandler(kafka_config)

    sns_cofig = get_sns_config(sns_config_path)
    log_hanfler_sns = SNSLogHandler(sns_cofig)

    log_format = '%(asctime)s - %(levelname)s - %(filename)s > %(funcName)s:%(lineno)d - %(message)s'

    formatter = logging.Formatter(
        fmt=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

    log_handler.setFormatter(formatter)
    if sns_cofig != None:
        logger.addHandler(log_hanfler_sns)

    if not hasattr(log_handler_kafka, "sender"):
        logger.addHandler(log_handler)
    else:
        logger.addHandler(log_handler_kafka)

    log_request_filter = LogRequestFilter()

    for handler in logging.getLogger().handlers:
        try:
            handler.addFilter(log_request_filter)
        except Exception as error:
            print(error)


def initial_config(config_path, sns_config_path):
    Config(config_path)

    try:
        init_sentry()
    except Exception as error:
        logging.error("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Internal, {
            "Exception: ": repr(error)
        }))

    config = Config.get_all()

    settings["max_buffer_size"] = config["limits"]["max_buffer_size"]

    if "logging" in config:
        init_logging(config["logging"], sns_config_path)

    logging.info("Set API configuration")

    api = config["api"]
    md_type = api["type"]
    
    url = environ.get("MDCLOUD_URL", "https://api.metadefender.com/v4")
    if url == "":
        url = api["url"]["cloud"]
    if md_type == "core":
        url = api["url"][md_type] if "url" in api and  "core" in api["url"] else "http://localhost:8008"
    if environ.get("MENLO_ENV", 'prod') == 'prod':
        url = api["url"]["cloud"]
        
    apikey = api["params"]["apikey"] if "params" in api and "apikey" in api["params"] else None

    env_apikey = os.environ.get('apikey')
    if env_apikey:
        apikey = env_apikey

    md_cls = MetaDefenderCoreAPI if md_type == "core" else MetaDefenderCloudAPI
    MetaDefenderAPI.config(url, apikey, md_cls)

    if "https" in config:
        if "load_local" in config["https"] and config["https"]["load_local"]:

            settings["ssl_options"] = {
                "certfile": config["https"]["crt"],
                "keyfile": config["https"]["key"],
            }

    if "server" in config:
        logging.info("Set Server configuration")
        server_details = config["server"]
        SERVER_PORT = server_details["port"] if "port" in server_details else SERVER_PORT
        HOST = server_details["host"] if "host" in server_details else HOST
        API_VERSION = server_details["api_version"] if "api_version" in server_details else HOST


def make_app():
    web_root = os.path.dirname(__file__) + '/../docs/'
    endpoints_list = [
        ('/', HealthCheckHandler),
        ("/docs/(.*)", tornado.web.StaticFileHandler, {
            "path": web_root,
            "default_filename": "Menlo Sanitization API.html"
        }),
        (API_VERSION + '/health', HealthCheckHandler),
        (API_VERSION + '/check', CheckExistingHandler),
        (API_VERSION + '/inbound', InboundMetadataHandler),
        (API_VERSION + '/submit', FileSubmitHandler),
        (API_VERSION + '/result', AnalysisResultHandler),
        (API_VERSION + '/file', RetrieveSanitizedHandler)
    ]
    return tornado.web.Application(endpoints_list)


def main():
    # ugly patch to address https://github.com/tornadoweb/tornado/issues/2608
    # asyncio won't work on Windows when using python 3.8+
    if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    initial_config('./config.yml', './metadefender_menlo/conf/sns-config.json')
    logging.info("Start the app: {0}:{1}".format(HOST, SERVER_PORT))

    app = make_app()
    http_server = tornado.httpserver.HTTPServer(app, **settings)
    http_server.listen(SERVER_PORT, HOST)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
