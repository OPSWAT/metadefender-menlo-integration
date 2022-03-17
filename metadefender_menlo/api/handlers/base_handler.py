from tornado.web import RequestHandler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
import json
import logging

class BaseHandler(RequestHandler):

    def initialize(self):
        self.metaDefenderAPI = MetaDefenderAPI.get_instance()

    def json_response(self, data, status_code=200):
        logging.info("{0} response: {1}".format(status_code, data))
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/json')
        self.write(json.dumps(data))

    def stream_response(self, data, status_code=200):  
        logging.info("{0} response: {1}".format(status_code, "sanitized file (binary data)"))      
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/octet-stream')
        self.write(data)
