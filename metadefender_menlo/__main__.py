import asyncio
import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from os import environ
import json
import aiohttp
from aiohttp import web
import sentry_sdk
from sentry_sdk.integrations.aiohttp import AioHttpIntegration
from metadefender_menlo.api.config import Config

from metadefender_menlo.api.handlers.health_check import health_check_route
from metadefender_menlo.api.handlers.check_existing import check_existing_route
from metadefender_menlo.api.handlers.stream_file_submit import stream_file_submit_route
from metadefender_menlo.api.handlers.analysis_result import analysis_result_route
from metadefender_menlo.api.handlers.retrieve_sanitized import retrieve_sanitized_route
# from metadefender_menlo.api.handlers.file_metadata import inbound_metadata_route
# from metadefender_menlo.api.handlers.file_submit import file_submit_route
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.log_handlers.kafka_log import KafkaLogHandler
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.handlers.base_handler import LogRequestFilter

def traces_sampler(sampling_context):
    """Filter healthcheck endpoint when sending transactions to sentry"""
    if sampling_context.get("aiohttp_request") and '/api/v1/health' in sampling_context["aiohttp_request"].path:
        return 0
    return 1


def init_sentry(env, sentry_dsn):
    if env != 'local' and sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                AioHttpIntegration(),
            ],
            environment=env,
            traces_sampler=traces_sampler,
        )


def get_kafka_config(kafka_config_path):
    try:
        kafka_config_file = open(kafka_config_path, encoding="utf-8")
        kafka_config = json.load(kafka_config_file)
        kafka_config_file.close()
        return kafka_config
    except Exception:
        return None


def init_logging(config):
    config_logging = config["logging"]
    if "enabled" not in config_logging or not config_logging["enabled"]:
        return

    logger = logging.getLogger()
    logging.getLogger('aiohttp.access').disabled = True
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

    if config['logging']['kafka']['enabled']:
        log_handler_kafka = KafkaLogHandler(config, config['logging']['kafka'])
        if hasattr(log_handler_kafka, "sender"):
            logger.addHandler(log_handler_kafka)
        else:
            logger.addHandler(log_handler)
    else:
        logger.addHandler(log_handler)

    if config['logging']['sns']['enabled']:
        log_hanfler_sns = SNSLogHandler(config['logging']['sns'])
        logger.addHandler(log_hanfler_sns)

    log_request_filter = LogRequestFilter()

    for handler in logging.getLogger().handlers:
        try:
            handler.addFilter(log_request_filter)
        except Exception as error:
            print(error)


def initial_config(config_path):
    Config(config_path)

    config = Config.get_all()

    try:
        init_sentry(config['env'], config['sentryDsn'])
    except Exception:
        logging.warning("Sentry not configured, skipping Sentry integration")

    if "logging" in config:
        init_logging(config)

    url = config['serverUrl']
    md_type = config["api"]["type"]
    apikey = config["apikey"]

    md_cls = MetaDefenderCoreAPI if md_type == "core" else MetaDefenderCloudAPI
    MetaDefenderAPI.config(config, url, apikey, md_cls)

    return config


def setup_ssl(config):
    if "https" in config and "load_local" in config["https"] and config["https"]["load_local"]:
        ssl_context = web.SSLContext()
        ssl_context.load_cert_chain(config["https"]["crt"], config["https"]["key"])
        return ssl_context
    return None


def setup_routes(app, config):
    # Set static file handler for docs
    web_root = os.path.dirname(__file__) + '/../docs/'
    app.router.add_static('/docs/', web_root)

    api_version = config['server']['api_version']
    
    # Add all route handlers
    app.router.add_get('/', health_check_route)
    app.router.add_get(api_version + '/health', health_check_route)
    app.router.add_post(api_version + '/submit', stream_file_submit_route)
    app.router.add_get(api_version + '/result', analysis_result_route)
    app.router.add_get(api_version + '/check', check_existing_route)
    app.router.add_get(api_version + '/file', retrieve_sanitized_route)
    # app.router.add_post(api_version + '/inbound', inbound_metadata_route)
    
    # Store config in app context
    app['config'] = config


async def main():

    config = initial_config('./config.yml')

    SERVER_HOST = config['server']['host']
    SERVER_PORT = config['server']['port']
    MAX_FILE_SIZE = config['limits']['max_file_size']

    app = web.Application(client_max_size=1024**2*MAX_FILE_SIZE)
    
    setup_routes(app, config)

    ssl_context = setup_ssl(config)
    
    # Start the server
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, SERVER_HOST, SERVER_PORT, ssl_context=ssl_context)
    await site.start()
    
    # Keep the server running
    logging.info(f"Running on http{'s' if ssl_context else ''}://{SERVER_HOST}:{SERVER_PORT}")
    
    # Set up shutdown event to gracefully close the server
    try:
        while True:
            await asyncio.sleep(3600)  # Keep alive
    except (KeyboardInterrupt, asyncio.CancelledError):
        print("Shutting down...")
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
