import logging
from aiohttp import web
from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class AnalysisResultHandler(BaseHandler):
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
            "method": "GET", "endpoint": "/api/v1/result/%s" % uuid}))

        json_response, http_status = await self.meta_defender_api.check_result(uuid, apikey, self.client_ip)

        try:
            json_response, http_status = await FileAnalyis().handle_response(http_status, json_response)
            return self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.meta_defender_api.service_name, TYPE.Response, {
                "error": repr(error)
            }), {'apikey': apikey})
            return self.json_response({}, 500)

async def analysis_result_route(request):
    handler = AnalysisResultHandler()
    return await handler.handle_get(request)
