import logging
from aiohttp import web
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.responses.check_existing import CheckExisting
from metadefender_menlo.api.log_types import TYPE

class CheckExistingHandler(BaseHandler):
    def __init__(self):
        super().__init__()

    async def handle_get(self, request):
        sha256 = request.query.get('sha256')
        if not sha256:
            return self.json_response({'error': 'SHA256 parameter is required'}, 400)

        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip

        apikey = request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "GET", "endpoint": "/api/v1/check?sha256=%s" % sha256}))

        json_response, http_status = await self.meta_defender_api.check_hash(sha256, apikey, self.client_ip)
        
        try:
            json_response, http_status = await CheckExisting(apikey).handle_response(http_status, json_response)
            return self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.meta_defender_api.service_name, TYPE.Response, {
                "error": repr(error)
            }), {'apikey': apikey})
            return self.json_response({}, 500)

async def check_existing_route(request):
    handler = CheckExistingHandler()
    return await handler.handle_get(request)
