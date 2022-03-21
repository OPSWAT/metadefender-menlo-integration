import yaml
import os
import asyncio
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
from metadefender_menlo.api.models.kafka_log import KafkaLogHandler
from dotenv import load_dotenv

import tornado.ioloop
import tornado.web

from metadefender_menlo.api.handlers.analysis_result import AnalysisResultHandler
from metadefender_menlo.api.handlers.file_metadata import InboundMetadataHandler
from metadefender_menlo.api.handlers.file_submit import FileSubmitHandler
from metadefender_menlo.api.handlers.retrieve_sanitized import RetrieveSanitizedHandler
from metadefender_menlo.api.handlers.check_existing import CheckExistingHandler
from metadefender_menlo.api.handlers.health_check import HealthCheckHandler

from metadefender_menlo.api.models.file_submit_body import FileSubmitBody
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI

SERVER_PORT = 3000
HOST = "0.0.0.0"
API_VERSION = "/api/v1"

settings = {}

def init_logging(config):    
    if "enabled" not in config or not config["enabled"]:
        return

    load_dotenv()
    
    logger = logging.getLogger()
    logger.setLevel(config["level"])
    logfile = config["logfile"]

    log_handler = TimedRotatingFileHandler(filename=logfile, when="h", interval=config["interval"], backupCount=config["backup_count"])
    log_handlerKafka = KafkaLogHandler()
    
    log_format = '%(asctime)s - %(levelname)s - %(filename)s > %(funcName)s:%(lineno)d - %(message)s'

    formatter = logging.Formatter(fmt=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')

    log_handler.setFormatter(formatter)

    logger.addHandler(log_handlerKafka)
    logger.addHandler(log_handler)

def initial_config():
    
    with open("config.yml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)

            if "logging" in config: 
                init_logging(config["logging"])

            logging.info("Set API configuration")

            api = config["api"]
            md_type = api["type"]
            url = api["url"][md_type] if "url" in api and md_type in api["url"] else "http://localhost:8008"
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
            
            
        except yaml.YAMLError as exc:
            logging.exception("Cannot load config file. Details: {0}".format(exc))

def make_app():
    logging.info("Define endpoints handlers")
    endpoints_list = [
        ('/', HealthCheckHandler),
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
    if sys.version_info[0]==3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    initial_config()
    
    app = make_app()
    
    logging.info("Start the app: {0}:{1}".format(HOST, SERVER_PORT))

    http_server = tornado.httpserver.HTTPServer(app, **settings)
    http_server.listen(SERVER_PORT, HOST)
    tornado.ioloop.IOLoop.current().start()

if __name__ == "__main__":
    main()