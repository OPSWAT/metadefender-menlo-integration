
from metadefender_menlo.api.responses.base_response import BaseResponse
import json


class SanitizedFile(BaseResponse):

    def __init__(self, apikey=''):
        super().__init__(apikey, [200, 204, 401, 403, 404, 405, 500])

        self._http_responses["204"] = self.__response204
        self._http_responses["401"] = self.__response401
        self._http_responses["403"] = self.__response403
        self._http_responses["404"] = self.__response400
        self._http_responses["405"] = self.__response501

    async def __response204(self, response, status_code):
        return (response, 204)

    async def __response400(self, response, status_code):
        if isinstance(response, (bytes, bytearray)):
            try:
                response = json.loads(response.decode('utf-8'))
            except Exception:
                pass
        return (response, 400)

    async def __response401(self, response, status_code):
        return ({}, 401)

    async def __response403(self, response, status_code):
        return (response, 403)

    async def __response501(self, response, status_code):
        return (response, 501)
