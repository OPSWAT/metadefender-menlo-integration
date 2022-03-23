from tornado.web import RequestHandler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
import json
import logging
import uuid
import json 
import contextvars

request_id_var = contextvars.ContextVar("request_id")

class BaseHandler(RequestHandler):
    def prepare(self):
        # If the request headers do not include a request ID, let's generate one.
        request_id = self.request.headers.get("request-id") or str(uuid.uuid4())
        request_id_var.set(request_id)
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

class MyFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get('-')
        return True