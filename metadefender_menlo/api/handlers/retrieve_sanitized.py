import logging
from aiohttp import web
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class RetrieveSanitizedHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    async def handle_get(self, request):
        uuid = request.query.get('uuid')
        if not uuid:
            return self.json_response({'error': 'UUID parameter is required'}, 400)

        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip

        apikey = request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid}))

        data, status_code = await self.meta_defender_api.retrieve_sanitized_file(uuid, apikey, self.client_ip)
        
        if status_code == 200:
            return self.stream_response(data, status_code)
        return self.json_response(data, status_code)

async def retrieve_sanitized_route(request):
    handler = RetrieveSanitizedHandler()
    return await handler.handle_get(request)
