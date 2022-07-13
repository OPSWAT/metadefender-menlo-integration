
from metadefender_menlo.api.responses.base_response import BaseResponse


class RetrieveSanitized(BaseResponse):

    def __init__(self, allowedResponses=None):

        allowedResponses = [200, 404,204, 405,403, 500]
        super().__init__(allowedResponses)

        self._http_responses["403"] = self.__response403
        self._http_responses["404"] = self.__response404
        self._http_responses["405"] = self.__response405
        self._http_responses["204"] = self.__response204

    def __response404(self, response, status_code):
        return (response, 400)
    
    def __response405(self, response, status_code):
        return (response, 501)
        
    def __response403(self, response, status_code):
        return (response, 403)
    def __response204(self, response, status_code):
        return (response, 204)
   
    
    