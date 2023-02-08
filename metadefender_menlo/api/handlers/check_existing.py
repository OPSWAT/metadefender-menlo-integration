import logging
from metadefender_menlo.api.responses.check_existing import CheckExisting
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class CheckExistingHandler(BaseHandler):

    async def get(self):
        sha256 = self.get_query_argument('sha256')

        apikey = self.request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format("MenloPlugin", "Request", {
            "method": "GET",
            "endpoint": "/api/v1/result/{0}".format(sha256)
        }))
        json_response, http_status = await self.metaDefenderAPI.hash_lookup(sha256, apikey, self.client_ip)
        json_response['sha256'] = sha256
        try:
            json_response, http_status = CheckExisting(
            ).handle_response(http_status, json_response)
            self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error)
            }))
            self.json_response({}, 500)
