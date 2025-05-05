import uuid
import logging
import contextvars
from aiohttp import web
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

request_id_var = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")

class BaseHandler:

    def __init__(self):
        self.meta_defender_api = MetaDefenderAPI.get_instance()
        self.client_ip = None

    @staticmethod
    async def prepare_request(request):
        # If the request headers do not include a request ID, let's generate one.
        request_id = request.headers.get("request-id") or str(uuid.uuid4())
        request_id_var.set(request_id)
        request_context.set(request)

        # Get client IP address
        client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.remote
        return client_ip

    def json_response(self, data, status_code=200):
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "status": status_code, "response": data}))
        
        if status_code == 204:
            return web.Response(status=status_code)
        
        return web.json_response(data, status=status_code)

    def stream_response(self, data, status_code=200):
        if status_code == 204:
            return web.Response(status=status_code)
        
        return web.Response(
            body=data, 
            status=status_code,
            headers={"Content-Type": "application/octet-stream"}
        )

class LogRequestFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get('-')
        record.request_info = request_context.get("")
        return True