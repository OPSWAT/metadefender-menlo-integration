import logging
from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class AnalysisResultHandler(BaseHandler):
    async def get(self):
        uuid = self.get_argument('uuid')

        apikey = self.request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "GET", "endpoint": "/api/v1/result/%s" % uuid}))

        json_response, http_status = await self.metaDefenderAPI.check_result(uuid, apikey, self.client_ip)
        try:
            json_response, http_status = FileAnalyis(
            ).handle_response(http_status, json_response)
            self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error)
            }))
            self.json_response({}, 500)
