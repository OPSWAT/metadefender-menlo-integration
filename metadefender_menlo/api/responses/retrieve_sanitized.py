
from metadefender_menlo.api.responses.base_response import BaseResponse


class RetrieveSanitized(BaseResponse):

    def __init__(self, apikey='', allowedResponses=None):

        allowedResponses = [200, 204, 401, 403, 404, 405, 500]
        super().__init__(apikey, allowedResponses)

        self._http_responses["204"] = self.__response204
        self._http_responses["403"] = self.__response403
        self._http_responses["404"] = self.__response400
        self._http_responses["405"] = self.__response501
        self._http_responses["401"] = self.__response401

    def __response204(self, response, status_code):
        return (response, 204)

    def __response400(self, response, status_code):
        return (response, 400)

    def __response401(self, response, status_code):
        return ({}, 401)

    def __response403(self, response, status_code):
        return (response, 403)

    def __response501(self, response, status_code):
        return (response, 501)
