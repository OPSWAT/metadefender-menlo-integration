
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

def traces_sampler(sampling_context):
    # filter healthcheck endpoint when sending transactions to sentry
    if '/api/v1/health' in sampling_context["tornado_request"].uri:
        return 0
    return 1


def init_sentry(env, sentry_dns):
    if env != 'local' and sentry_dns:
        sentry_sdk.init(
            dsn=sentry_dns,
            integrations=[
                TornadoIntegration(),
            ],
            environment=env,
            traces_sampler=traces_sampler,
        )

def get_sns_config(env, rule, config_path):
    if rule == "cdr":
        rule = "_" + rule
    else:
        rule = ""

    environment_name = "menlo_middleware_" + env + rule

    try:
        with open(config_path, encoding="utf-8") as sns_config_file:
            sns_config = json.load(sns_config_file)

        if environment_name in sns_config:
            connection = sns_config[environment_name]
            return {
                "arn": connection["arn"],
                "region": connection["region"]
            }
    except Exception as _error:
        pass

    return None


def get_kafka_config(kafka_config_path):
    try:
        kafka_config_file = open(kafka_config_path, encoding="utf-8")
        kafka_config = json.load(kafka_config_file)
        kafka_config_file.close()
        return kafka_config
    except Exception as error:
        return None

def init_logging(config, sns_config_path):
    config_logging = config["logging"]
    if "enabled" not in config_logging or not config_logging["enabled"]:
        return

    load_dotenv()
    logger = logging.getLogger()
    logging.getLogger('tornado.access').disabled = True
    logging.getLogger('kafka.conn').disabled = True
    logging.getLogger('kafka.access').disabled = True
    logger.setLevel(config_logging["level"])
    logfile = config_logging["logfile"]
    
    # create log handlers
    log_handler = TimedRotatingFileHandler(
        filename=logfile, when="h", interval=config_logging["interval"], backupCount=config_logging["backup_count"])

    log_format = '%(asctime)s - %(levelname)s - %(filename)s > %(funcName)s:%(lineno)d - %(message)s'
    formatter = logging.Formatter(
        fmt=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

    log_handler.setFormatter(formatter)

    kafka_config = get_kafka_config('./metadefender_menlo/conf/kafka-config.json')
    if kafka_config:
        log_handler_kafka = KafkaLogHandler(config, kafka_config)
        if hasattr(log_handler_kafka, "sender"):
            logger.addHandler(log_handler_kafka)
        else:
            logger.addHandler(log_handler)
    else:
        logger.addHandler(log_handler)

    sns_cofig = get_sns_config(config['env'], config['scanRule'], sns_config_path)
    if sns_cofig != None:
        log_hanfler_sns = SNSLogHandler(sns_cofig)
        logger.addHandler(log_hanfler_sns)

    log_request_filter = LogRequestFilter()

    for handler in logging.getLogger().handlers:
        try:
            handler.addFilter(log_request_filter)
        except Exception as error:
            print(error)


def initial_config(config_path, sns_config_path):
    Config(config_path)

    config = Config.get_all()

    try:
        init_sentry(config['env'], config['sentryDns'])
    except Exception as error:
        logging.error("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Internal, {
            "Exception: ": repr(error)
        }))

    settings["max_buffer_size"] = config["limits"]["max_buffer_size"]

    if "logging" in config:
        init_logging(config, sns_config_path)

    logging.info("Set API configuration")

    url = config['serverUrl']
    md_type = config["api"]["type"]
    apikey = config["apikey"]

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

    return config


def make_app(config):
    web_root = os.path.dirname(__file__) + '/../docs/'
    endpoints_list = [
        ('/', HealthCheckHandler, {'newConfig': config}),
        ("/docs/(.*)", tornado.web.StaticFileHandler, {
            "path": web_root,
            "default_filename": "Menlo Sanitization API.html"
        }),
        (API_VERSION + '/health', HealthCheckHandler, {'newConfig': config}),
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

    config = initial_config('./config.yml', './metadefender_menlo/conf/sns-config.json')
    logging.info("Start the app: {0}:{1}".format(HOST, SERVER_PORT))

    app = make_app(config)
    http_server = tornado.httpserver.HTTPServer(app, **settings)
    http_server.listen(SERVER_PORT, HOST)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
