import logging
import os
import resource
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from metadefender_menlo.logging import init_logging
from metadefender_menlo.api.config import Config
from metadefender_menlo.api.handlers.health_handler import health_handler
from metadefender_menlo.api.handlers.check_handler import check_handler
from metadefender_menlo.api.handlers.submit_handler import submit_handler
from metadefender_menlo.api.handlers.result_handler import result_handler
from metadefender_menlo.api.handlers.sanitized_file_handler import file_handler
from metadefender_menlo.api.handlers.inbound_handler import inbound_handler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.metadefender.metadefender_cloud_api import MetaDefenderCloudAPI
from metadefender_menlo.api.metadefender.metadefender_core_api import MetaDefenderCoreAPI
from metadefender_menlo.log_handlers.sentry_log import init_sentry

app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)

def setup_resource_limits(config):
    """Set resource limits based on configuration."""
    try:
        resource_cfg = config.get("resource", {})
        softlimit = resource_cfg.get("softlimit")
        hardlimit = resource_cfg.get("hardlimit")
        if resource_cfg.get("enabled") and softlimit and hardlimit:
            resource.setrlimit(resource.RLIMIT_NOFILE, (softlimit, hardlimit))
            logging.info(f"Applied file descriptor limits: soft={softlimit}, hard={hardlimit}")
    except Exception as e:
        logging.warning(f"Failed to set resource limits: {e}")

def setup_config(config_path):
    Config(config_path)

    config = Config.get_all()

    try:
        if 'sentryDsn' in config:
            init_sentry(config['env'], config['sentryDsn'])
    except Exception:
        logging.warning("Sentry not configured, skipping Sentry integration")

    try:
        if 'logging' in config:
            init_logging(config)
    except Exception:
        logging.warning("Logging not configured, skipping logger configuration")

    setup_resource_limits(config)

    url = config['serverUrl']
    md_type = config["api"]["type"]
    apikey = config["apikey"]

    md_cls = MetaDefenderCoreAPI if md_type == "core" else MetaDefenderCloudAPI
    logging.info(f"Using MetaDefender API: {md_cls.__name__}")
    MetaDefenderAPI.config(config, url, apikey, md_cls)

    return config


def setup_routes(config):
    # Set static file handler for docs
    web_root = os.path.dirname(__file__) + '/../docs/'
    app.mount('/docs', StaticFiles(directory=web_root), name="docs")

    api_version = config['server']['api_version']

    app.add_api_route(path='/', endpoint=health_handler, methods=["GET"], response_model=dict)
    app.add_api_route(path=api_version + '/health', endpoint=health_handler, methods=["GET"], response_model=dict)
    app.add_api_route(path=api_version + '/submit', endpoint=submit_handler, methods=["POST"], response_model=dict)
    app.add_api_route(path=api_version + '/result', endpoint=result_handler, methods=["GET"], response_model=dict)
    app.add_api_route(path=api_version + '/check', endpoint=check_handler, methods=["GET"], response_model=dict)
    app.add_api_route(path=api_version + '/file', endpoint=file_handler, methods=["GET"], response_model=dict)
    app.add_api_route(path=api_version + '/inbound', endpoint=inbound_handler, methods=["POST"], response_model=dict)

def setup_ssl(config):
    ssl_keyfile = None
    ssl_certfile = None
    if "https" in config and "load_local" in config["https"] and config["https"]["load_local"]:
        ssl_keyfile = config["https"]["key"]
        ssl_certfile = config["https"]["crt"]

    return ssl_keyfile, ssl_certfile

def main():
    config = setup_config('./config.yml')
    
    app.state.config = config

    setup_routes(config)

    ssl_keyfile, ssl_certfile = setup_ssl(config)
    
    SERVER_HOST = config['server']['host']
    SERVER_PORT = config['server']['port']
    protocol = "https" if ssl_certfile else "http"
    logging.info(f"Running on {protocol}://{SERVER_HOST}:{SERVER_PORT}")
    
    uvicorn.run(
        app, 
        host=SERVER_HOST, 
        port=SERVER_PORT,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile
    )

if __name__ == "__main__":
    main()
