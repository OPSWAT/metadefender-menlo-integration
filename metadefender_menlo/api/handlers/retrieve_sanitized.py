from metadefender_menlo.api.responses.retrieve_sanitized import RetrieveSanitized
from metadefender_menlo.api.handlers.base_handler import BaseHandler
import logging

class RetrieveSanitizedHandler(BaseHandler):
    async def get(self):
        uuid = self.get_argument('uuid')
        apikey = self.request.headers.get('Authorization')
        logging.info("GET /api/v1/file/{0}".format(uuid))   
        
        file, status_code = await self.metaDefenderAPI.retrieve_sanitized_file(uuid, apikey, self.client_ip)
        
        sanitized_file, status = RetrieveSanitized().handle_response(status_code, file)
        self.stream_response(sanitized_file, status)
