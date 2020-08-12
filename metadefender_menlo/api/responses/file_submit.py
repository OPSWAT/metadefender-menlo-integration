
from metadefender_menlo.api.responses.base_response import BaseResponse

class FileSubmit(BaseResponse):

    def __init__(self, allowedResponses=None):
        
        allowedResponses = [200, 400, 401, 411, 422, 500, 503]
        super().__init__(allowedResponses)

        
        self._http_responses["200"] = self.__response200
        self._http_responses["411"] = self.__response411
        self._http_responses["400"] = self.__response400
        self._http_responses["401"] = self.__response400

    def __response200(self, json_response, status_code):
        translation = {
            'uuid': '{0}',
            'result': '{0}'
        }

        if 'data_id' in json_response: 
            
            self._translate('uuid', translation, json_response['data_id'])
            self._translate('result', translation, 'accepted')
        else:
            del translation['uuid']
            self._translate('result', translation, 'skip')



        return (translation, 200)

    def __response411(self, json_response, status_code):
        return (json_response, 422)

    def __response400(self, json_response, status_code):
        # invalid APIkey -> respond with Unauthorized
        return (json_response, 401)
