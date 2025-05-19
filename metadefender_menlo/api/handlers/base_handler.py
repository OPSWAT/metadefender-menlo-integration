import uuid
import logging
import contextvars
from fastapi import Response
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

request_id_context = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")

class BaseHandler:

    def __init__(self):
        self.meta_defender_api = MetaDefenderAPI.get_instance()
        self.client_ip = None
        self.apikey = None

    async def prepare_request(self, request):
        request_context.set(request)
        request_id_context.set(request.headers.get("request-id") or str(uuid.uuid4()))

        try:
            self.client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host
        except Exception:
            pass

        self.apikey = request.headers.get('Authorization')

    def json_response(self, response, json_response, status_code=200):
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "status": status_code, "response": json_response}))
        
        response.status_code = status_code
        
        if status_code == 204:
            return {}
        
        return json_response

    def stream_response(self, data, status_code=200):
        if status_code == 204:
            return Response(status_code=status_code)
        
        return Response(
            content=data, 
            status_code=status_code,
            headers={"Content-Type": "application/octet-stream"}
        )