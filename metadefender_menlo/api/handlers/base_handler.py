import json
import uuid
import logging
import contextvars
from tornado.web import RequestHandler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE
request_id_var = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")
class BaseHandler(RequestHandler):
    def prepare(self):
        # If the request headers do not include a request ID, let's generate one.
        request_id = self.request.headers.get(
            "request-id") or str(uuid.uuid4())
        request_id_var.set(request_id)
        request_context.set(self.request)

    def initialize(self):
        self.metaDefenderAPI = MetaDefenderAPI.get_instance()

        client_ip = self.request.headers.get(
            "X-Real-IP") or self.request.headers.get("X-Forwarded-For") or self.request.remote_ip
        self.client_ip = client_ip

    def json_response(self, data, status_code=200):
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "status": status_code, "response": data}))
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/json')
        if status_code != 204:
            self.write(json.dumps(data))

    def stream_response(self, data, status_code=200):
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/octet-stream')
        if status_code != 204:
            self.write(data)

class LogRequestFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get('-')
        record.request_info = request_context.get("")
        return True