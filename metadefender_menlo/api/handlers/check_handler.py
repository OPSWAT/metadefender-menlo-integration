import logging
from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.responses.check_existing import CheckExisting
from metadefender_menlo.api.log_types import SERVICE, TYPE

class CheckHandler(BaseHandler):
    """
    Handler for checking the status of a file using its SHA256 hash.
    """
    def __init__(self, config=None):
        super().__init__(config)
        if config and config['timeout']['check']['enabled']:
            self.handler_timeout = config['timeout']['check']['value']

    async def process_result(self, sha256: str):
        json_response, http_status = await self.meta_defender_api.check_hash(sha256, self.apikey, self.client_ip)
        json_response, http_status = await CheckExisting(self.apikey).handle_response(json_response, http_status)
        return json_response, http_status
    
    async def handle_get(self, request: Request, response: Response):
        sha256 = request.query_params.get('sha256')
        if not sha256:
            return self.json_response(response, {'error': 'SHA256 parameter is required'}, 400)

        self.prepare_request(request)
        
        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "GET", "endpoint": "/api/v1/check?sha256=%s" % sha256}
        ))
        
        try:
            json_response, http_status = await self.process_result_with_timeout(sha256)
            return self.json_response(response, json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def check_handler(request: Request, response: Response):
    return await CheckHandler(request.app.state.config).handle_get(request, response)
