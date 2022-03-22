from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
import logging
import json 
class AnalysisResultHandler(BaseHandler):    

    async def get(self):        
        uuid = self.get_argument('uuid')        
        logging.info(json.dumps({'msg':'GET /api/v1/result/{0}'.format(uuid),"id":self.id}))

        json_response, http_status = await self.metaDefenderAPI.check_result(uuid,self.id)
        json_response, http_status = FileAnalyis().handle_response(http_status, json_response)
        self.json_response(json_response, http_status)
       
