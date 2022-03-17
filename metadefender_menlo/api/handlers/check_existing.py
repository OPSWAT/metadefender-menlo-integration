from metadefender_menlo.api.responses.check_existing import CheckExisting
from metadefender_menlo.api.handlers.base_handler import BaseHandler
import logging

class CheckExistingHandler(BaseHandler):    

    async def get(self):        
        sha256 = self.get_query_argument('sha256') 
        apikey = self.request.headers.get('Authorization')        
        logging.info("GET /api/v1/result/{0}".format(sha256))

        json_response, http_status = await self.metaDefenderAPI.hash_lookup(sha256, apikey)
        json_response, http_status = CheckExisting().handle_response(http_status, json_response)
        self.json_response(json_response, http_status)
        
    