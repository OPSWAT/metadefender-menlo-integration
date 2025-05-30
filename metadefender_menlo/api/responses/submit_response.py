
import logging

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.responses.base_response import BaseResponse


class SubmitResponse(BaseResponse):

    def __init__(self, apikey=''):
        super().__init__(apikey, [200, 400, 401, 411, 422, 429, 500, 503])

        self._http_responses["200"] = self.__response200
        self._http_responses["400"] = self.__response400
        self._http_responses["401"] = self.__response401
        self._http_responses["429"] = self.__response401
        self._http_responses["411"] = self.__response422

    async def __response200(self, json_response, status_code):
        translation = {
            'uuid': '{0}',
            'result': '{0}'
        }
        try:
            if 'data_id' in json_response:

                self._translate('uuid', translation, json_response['data_id'])
                self._translate('result', translation, 'accepted')
            else:
                del translation['uuid']
                self._translate('result', translation, 'skip')

            return (translation, 200)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                SERVICE.MetaDefenderAPI,
                TYPE.Response,
                {"error": repr(error), "MdCloudResponse": json_response}
            ), {'apikey': self._apikey})
            return ({}, 500)

    async def __response400(self, json_response, status_code):
        # invalid APIkey -> respond with Unauthorized
        return (json_response, 400)

    async def __response401(self, json_response, status_code):
        return ({}, 401)

    async def __response422(self, json_response, status_code):
        return (json_response, 422)
        
