import logging
import asyncio
from fastapi import Request, Response
from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class ResultHandler(BaseHandler):
    """
    Handler for retrieving the result of a file analysis using its UUID.
    """

    def __init__(self, config=None):
        super().__init__(config)
        if self.config and self.config['timeout']['result']['enabled']:
            self.handler_timeout = self.config['timeout']['result']['value']

    async def process_result(self, uuid: str):
        """Get result from MetaDefender and process the response"""
        json_response, http_status = await self.meta_defender_api.check_result(uuid, self.apikey, self.client_ip)
        json_response, http_status = await FileAnalyis(self.apikey).handle_response(json_response, http_status)
        return json_response, http_status

    async def handle_get(self, request: Request, response: Response):
        uuid = request.query_params.get('uuid')
        if not uuid:
            return self.json_response(response, {'error': 'UUID parameter is required'}, 400)
        
        if self.allowlist_handler.is_allowlist_enabled(uuid):
            allowlist_response, status_code = self.allowlist_handler.is_in_allowlist(uuid)
            if allowlist_response is not None:
                return self.json_response(response, allowlist_response, status_code)
        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "GET", "endpoint": "/api/v1/result/%s" % uuid}
        ))
        
        self.prepare_request(request)

        try:
            json_response, http_status = await self.process_result_with_timeout(uuid)
            return self.json_response(response, json_response, http_status)
        except asyncio.TimeoutError:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": f"Timeout while retrieving result for {uuid}"}
            ))
            return self.json_response(response, {
                'result': 'completed',
                'outcome': 'error',
                'report_url': '',
                'filename': '',
                'modifications': [f'Timeout while retrieving result for {uuid}']
            }, 200)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def result_handler(request: Request, response: Response):
    return await ResultHandler(request.app.state.config).handle_get(request, response)
