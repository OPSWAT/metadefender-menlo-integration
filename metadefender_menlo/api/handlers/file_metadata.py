import logging
import json
from aiohttp import web
from metadefender_menlo.api.handlers.base_handler import BaseHandler

class InboundMetadataHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    async def handle_post(self, request):
        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip

        apikey = request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "POST", "endpoint": "/api/v1/inbound"}))

        # Check and process request body
        if request.content_type.startswith('multipart/'):
            # Process multipart form data
            reader = await request.multipart()
            metadata = {}
            
            # Parse form fields
            field = await reader.next()
            while field is not None:
                if field.name != 'file':
                    # Read form field value
                    value = await field.text()
                    metadata[field.name] = value
                
                field = await reader.next()
        else:
            # Process JSON data
            try:
                metadata = await request.json()
            except json.JSONDecodeError:
                return self.json_response({"error": "Invalid JSON format"}, 400)

        # Submit metadata to API
        json_response, http_status = await self.meta_defender_api.inbound_file(
            apikey, metadata, self.client_ip)

        try:
            json_response, http_status = await FileInbound().handle_response(http_status, json_response)
            return self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.meta_defender_api.service_name, TYPE.Response, {
                "error": repr(error)
            }), {'apikey': apikey})
            return self.json_response({}, 500)

async def inbound_metadata_route(request):
    handler = InboundMetadataHandler()
    return await handler.handle_post(request)