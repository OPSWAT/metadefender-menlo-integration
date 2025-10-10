import logging
import asyncio
from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class SanitizedFileHandler(BaseHandler):
    """
    Handler for retrieving sanitized files from MetaDefender.
    """

    def __init__(self, config=None):
        super().__init__(config)
        if config and config['timeout']['sanitized']['enabled']:
            self.handler_timeout = config['timeout']['sanitized']['value']

    async def process_result(self, uuid: str):
        resp, http_status, client = await self.meta_defender_api.sanitized_file(uuid, self.apikey, self.client_ip)
        
        return resp, http_status, client

    async def handle_get(self, request: Request, response: Response):
        uuid = request.query_params.get('uuid')
        if not uuid:
            return self.json_response(response, {'error': 'UUID parameter is required'}, 400)

        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid}
        ))

        self.prepare_request(request)

        resp = None
        client = None
        http_status = None

        try:
            resp, http_status, client = await self.process_result_with_timeout(uuid)
            if http_status == 200:
                return self.stream_response(resp, client, http_status)
            
            logging.info("{0} > {1} > {2}".format(
                SERVICE.MenloPlugin, 
                TYPE.Request, 
                {"method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid, "http_status": http_status}
            ))

            return self.json_response(response, {}, http_status)
        except asyncio.TimeoutError:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": "Timeout while retrieving sanitized file"}
            ))
            return self.json_response(response, {}, 500)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Internal, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)
        finally:
            if http_status != 200:
                if hasattr(resp, "aclose"):
                    await resp.aclose()

async def file_handler(request: Request, response: Response):
    return await SanitizedFileHandler(request.app.state.config).handle_get(request, response)
