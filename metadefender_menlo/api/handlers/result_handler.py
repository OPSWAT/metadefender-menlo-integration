import logging
from fastapi import Request, Response
from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class ResultHandler(BaseHandler):
    """
    Handler for retrieving the result of a file analysis using its UUID.
    """
    def __init__(self):
        super().__init__()

    async def handle_get(self, request: Request, response: Response):

        uuid = request.query_params.get('uuid')
        if not uuid:
            return self.json_response(response, {'error': 'UUID parameter is required'}, 400)

        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "GET", "endpoint": "/api/v1/result/%s" % uuid}
        ))
        
        await self.prepare_request(request)

        try:
            json_response, http_status = await self.meta_defender_api.check_result(uuid, self.apikey, self.client_ip)
            json_response, http_status = await FileAnalyis(self.apikey).handle_response(json_response, http_status)
            return self.json_response(response, json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def result_handler(request: Request, response: Response):
    return await ResultHandler().handle_get(request, response)
