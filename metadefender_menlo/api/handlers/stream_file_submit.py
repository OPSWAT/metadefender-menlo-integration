import json
from aiohttp import web, ClientSession
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.responses.file_submit import FileSubmit

class StreamFileSubmit(BaseHandler):
    def __init__(self):
        super().__init__()
        self.upstream_url = "https://api.metadefender.com/v4/file"

    async def handle_post(self, request):
        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip
        
        # Check if request is multipart
        if not request.content_type.startswith('multipart/'):
            return self.json_response({"error": "Content-Type must be multipart/form-data"}, 400)

        apikey = request.headers.get('Authorization')
        
        # Stream the request directly to MetaDefender
        async with ClientSession() as session:
            # Forward the request with the same content-type
            upstream_headers = {
                'Content-Type': request.headers.get('Content-Type'),
                'apikey': apikey,
                'x-forwarded-for': self.client_ip,
                'x-real-ip': self.client_ip,
                'rule': 'multiscan,sanitize'
            }
            
            # Forward the complete request body
            body = await request.read()
            
            async with session.post(
                self.upstream_url,
                headers=upstream_headers,
                data=body
            ) as resp:
                # Return the response from upstream
                response_body = await resp.json()
                json_response, http_status = await FileSubmit().handle_response(resp.status, response_body)
                return self.json_response(json_response, http_status)

async def stream_file_submit_route(request):
    handler = StreamFileSubmit()
    return await handler.handle_post(request)