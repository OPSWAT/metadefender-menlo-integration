import logging
from metadefender_menlo.api.responses.retrieve_sanitized import RetrieveSanitized
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE


class RetrieveSanitizedHandler(BaseHandler):
    async def get(self):
        uuid = self.get_argument('uuid')

        apikey = self.request.headers.get('Authorization')
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
            "method": "GET", "endpoint": "/api/v1/file/%s" % uuid}))

        file, status_code = await self.metaDefenderAPI.retrieve_sanitized_file(uuid, apikey)
        try:
            sanitized_file, status = await RetrieveSanitized(apikey).handle_response(status_code, file)
            self.stream_response(sanitized_file, status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.metaDefenderAPI.service_name, TYPE.Response, {
                "error": repr(error)
            }), {'apikey': apikey})
            self.json_response({}, 500)
