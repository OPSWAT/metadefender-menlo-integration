import logging
import asyncio
from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

class SanitizedFileHandler(BaseHandler):
    """
    Handler for retrieving sanitized files from MetaDefender.
    """
    resp = None
    client = None
    http_status = None

    def __init__(self):
        super().__init__()

    async def _get_and_process_result(self, uuid: str):
        resp, http_status, client = await self.meta_defender_api.sanitized_file(uuid, self.apikey, self.client_ip)
        
        return resp, http_status, client

    async def handle_api_request_with_timeout(self, uuid: str, response: Response):
        try:
            timeout_value = None
            try:
                if self.sanitized_file_endpoint_timeout is not None:
                    timeout_value = float(self.sanitized_file_endpoint_timeout)
            except Exception:
                timeout_value = None

            if timeout_value is not None:
                self.resp, self.http_status, self.client = await asyncio.wait_for(
                    self._get_and_process_result(uuid),
                    timeout=timeout_value
                )
            else:
                self.resp, self.http_status, self.client = await self._get_and_process_result(uuid)

            if self.http_status == 200:
                return self.stream_response(self.resp, self.client, self.http_status)

            logging.info("{0} > {1} > {2}".format(
                SERVICE.MenloPlugin, 
                TYPE.Request, 
                {"method": "GET", "endpoint": "/api/v1/file?uuid=%s" % uuid, "http_status": self.http_status}
            ))

            return self.json_response(response, {}, self.http_status)
        except asyncio.TimeoutError:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": "Timeout while retrieving sanitized file"}
            ))
            return self.json_response(response, {}, 500)

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
            return await self.handle_api_request_with_timeout(uuid, response)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Internal, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)
        finally:
            if self.http_status != 200:
                if hasattr(self.resp, "aclose"):
                    await self.resp.aclose()
                if hasattr(self.client, "aclose"):
                    await self.client.aclose()

async def file_handler(request: Request, response: Response):
    return await SanitizedFileHandler().handle_get(request, response)
