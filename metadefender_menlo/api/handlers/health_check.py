from metadefender_menlo.api.handlers.base_handler import BaseHandler
import logging
import json
from metadefender_menlo.api.log_types import SERVICE, TYPE
from os import environ

class HealthCheckHandler(BaseHandler):
    def get(self):
        logging.debug("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, TYPE.Internal, {"message": "GET /health > OK!"}))
        self.set_status(200)
        self.set_header("Content-Type", 'application/json')
        self.write(json.dumps({
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "1.1.0",
            "rule": environ.get("MDCLOUD_RULE","multiscan, sanitize, unarchive")
        }))
