from metadefender_menlo.api.handlers.base_handler import BaseHandler
import logging
import json

class HealthCheckHandler(BaseHandler):
    def get(self):        
        logging.debug("GET /health > OK!")     
        self.set_status(200)
        self.set_header("Content-Type", 'application/json')
        self.write(json.dumps({
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "1.1.0"
        }))
