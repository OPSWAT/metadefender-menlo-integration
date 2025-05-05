import logging
import json
import os
from aiohttp import web
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.responses.file_submit import FileSubmit
from metadefender_menlo.api.log_types import SERVICE, TYPE

class FileSubmitHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    async def handle_post(self, request):
        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip

        apikey = request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "POST", "endpoint": "/api/v1/submit"}))

        # Check if request is multipart
        if not request.content_type.startswith('multipart/'):
            return self.json_response({"error": "Content-Type must be multipart/form-data"}, 400)

        # Process form data
        reader = await request.multipart()
        metadata = {}
        file_field = None
        file_name = None
        file_content = None

        # Parse form fields
        field = await reader.next()
        while field is not None:
            if field.name != 'file':
                # Read form field value
                value = await field.text()
                metadata[field.name] = value
            else:
                # Save file details for later processing
                file_field = field
                file_name = field.filename
                # Read file content into memory
                file_content = await field.read()
            
            field = await reader.next()
            
        if not file_field:
            return self.json_response({"error": "No file uploaded"}, 400)

        # Submit file to API
        json_response, http_status = await self.meta_defender_api.submit_file(
            file_name, file_content, apikey, metadata, self.client_ip)

        try:
            json_response, http_status = await FileSubmit().handle_response(http_status, json_response)
            return self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.meta_defender_api.service_name, TYPE.Response, {
                "error": repr(error)
            }), {'apikey': apikey})
            return self.json_response({}, 500)

async def file_submit_route(request):
    handler = FileSubmitHandler()
    return await handler.handle_post(request)
