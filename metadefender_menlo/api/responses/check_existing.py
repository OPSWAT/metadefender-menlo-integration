
from metadefender_menlo.api.responses.base_response import BaseResponse
import logging
from metadefender_menlo.api.log_types import SERVICE, TYPE


class CheckExisting(BaseResponse):

    def __init__(self, allowedResponses=None):

        allowedResponses = [200, 400, 401, 404, 500]
        super().__init__(allowedResponses)

        self._http_responses["200"] = self.__response200
        self._http_responses["400"] = self.__response400
        self._http_responses["401"] = self.__response401
        self._http_responses["404"] = self.__response400

    def __response200(self, response, status_code):
        translation = {
            'uuid': '{0}',
            'result': '{0}'
        }
        try:
            if 'data_id' in response:

                self._translate('uuid', translation, response['data_id'])
                self._translate('result', translation, 'found')

                return (translation, status_code)
            else:
                return (response, 404)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error), "MdCloudResponse": response
            }))
            return ({}, 500)

    def __response400(self, response, status_code):
        return ({
            'uuid': response['sha256'],
            'result': '404'
        }, 200)
        
    def __response401(self, response, status_code):
        return ({}, 401)
