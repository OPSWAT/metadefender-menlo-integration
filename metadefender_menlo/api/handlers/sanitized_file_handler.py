import logging
from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class SanitizedFileHandler(BaseHandler):
    """
    Handler for retrieving sanitized files from MetaDefender.
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
            {"method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid}
        ))

        await self.prepare_request(request)

        try:
            resp, http_status, client = await self.meta_defender_api.sanitized_file(uuid, self.apikey, self.client_ip)
            
            if http_status == 200:
                return self.stream_response(resp, client, http_status)
            
            logging.info("{0} > {1} > {2}".format(
                SERVICE.MenloPlugin, 
                TYPE.Request, 
                {"method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid, "http_status": http_status}
            ))

            return self.json_response(response, {}, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Internal, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def file_handler(request: Request, response: Response):
    return await SanitizedFileHandler().handle_get(request, response)
