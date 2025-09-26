import uuid
import logging
import contextvars
import yaml
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask
import boto3
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE

request_id_context = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)
    
domains_cache = {}
dynamodb = None
table = None

if config['allowlist'].get('enabled'):
    try:
        session = boto3.Session(profile_name=config['allowlist'].get('aws_profile', 'default'))
        dynamodb = session.resource('dynamodb')
        table = dynamodb.Table(config['allowlist']['db_table_name'])
    except Exception:
        dynamodb = None
        table = None

class BaseHandler:
    """
    Base handler class that provides common functionality for all handlers.
    """
    config = config
    domains_cache = domains_cache
    dynamodb = dynamodb
    table = table

    def __init__(self):
        self.meta_defender_api = MetaDefenderAPI.get_instance()
        self.client_ip = None
        self.apikey = None
    
    @classmethod
    def get_cached_domains(self, api_key: str) -> list:
        """Get cached domains for an API key"""
        if not self.dynamodb:
            return []
            
        if api_key not in self.domains_cache:
            api_key_response = self.table.get_item(Key={'id': f'APIKEY#{api_key}'})
            self.domains_cache[api_key] = api_key_response.get('Item', {}).get('domains', [])
        return self.domains_cache.get(api_key, [])

    async def prepare_request(self, request):
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