import logging
import json
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class HealthCheckHandler(BaseHandler):

    settings = None

    def initialize(self, newConfig):
        self.settings = newConfig
        return super().initialize()

    def get(self):
        logging.debug("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, TYPE.Internal, {"message": "GET /health > OK!"}))
        self.set_status(200)
        self.set_header("Content-Type", 'application/json')
        self.write(json.dumps({
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "1.5.8",
            "commitHash": self.settings['commitHash'],
            "rule": self.settings['scanRule']
        }))
