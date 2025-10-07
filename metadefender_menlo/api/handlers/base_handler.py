import asyncio
import uuid
import logging
import contextvars
from metadefender_menlo.api.utils.domain_allowlist import DomainAllowlistUtils
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

request_id_context = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")

class BaseHandler:
    """
    Base handler class that provides common functionality for all handlers.
    """

    def __init__(self, config = None):
        self.meta_defender_api = MetaDefenderAPI.get_instance()
        self.client_ip = None
        self.apikey = None
        self.handler_timeout = None
        self.config = config
        self.allowlist_handler = DomainAllowlistUtils(config)
    
    def prepare_request(self, request):
        """ 
        Prepare the request context and extract necessary headers.
        This method sets the request context and extracts the client IP and API key from the request headers.
        It also sets a unique request ID if not provided in the headers.

        :param request: The incoming request object.
        :return: None
        """
        request_context.set(request)
        request_id_context.set(request.headers.get("request-id") or str(uuid.uuid4()))

        try:
            self.client_ip = request.headers.get("X-Real-IP") or request.headers.get("X-Forwarded-For") or request.client.host
        except Exception:
            pass

        self.apikey = request.headers.get('Authorization')

    def json_response(self, response, json_response, status_code=200):
        """
        Prepare a JSON response with the given status code and response data.

        :param response: The response object to set the JSON response on.
        :param json_response: The JSON data to return in the response.
        :param status_code: The HTTP status code for the response.
        :return: The JSON response data.
        """
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "type": "json", "status": status_code, "response": json_response
        }))
        
        response.status_code = status_code
        
        if status_code == 204:
            return {}
        
        return json_response

    def stream_response(self, resp, client, status_code=200):
        """
        Prepare a streaming response from the given response object.
        
        :param resp: The response object containing the stream data.
        :param client: The client object used for cleanup after streaming.
        :param status_code: The HTTP status code for the response.
        :return: A StreamingResponse object that streams the response data.
        """
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "type": "stream", "status": status_code
        }))
        
        async def cleanup():
                await resp.aclose()
                await client.aclose()

        return StreamingResponse(
            resp.aiter_raw(),
            media_type=resp.headers.get("Content-Type", "application/octet-stream"),
            headers={
                "Content-Disposition": resp.headers.get(
                    "Content-Disposition", 'attachment; filename="downloaded.bin"'
                )
            },
            background=BackgroundTask(cleanup)
        )
    
    async def process_result_with_timeout(self, *args):
        """Process the result with an optional timeout. Subclasses should implement process_result."""
        if self.handler_timeout is not None:
            return await asyncio.wait_for(
                self.process_result(*args),
                timeout=self.handler_timeout
            )
        else:
            return await self.process_result(*args)
        
    async def process_result(self):
        """Process the result. This method should be implemented by subclasses."""
        raise NotImplementedError("_get_and_process_result must be implemented by subclasses")