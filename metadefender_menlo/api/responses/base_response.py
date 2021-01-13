

class BaseResponse(object):

    _allowedResponses = []
    _http_responses = {}

    
    def __init__(self, allowedResponses=None):

        self.__allowedResponses = allowedResponses

        for code in allowedResponses:
            status_code = str(code)
            self._http_responses[status_code] = self._default_response
    
    def handle_response(self, status_code, raw_response):
        if status_code not in self.__allowedResponses:  
            raise Exception('Not Allowed', 'No such response code allowed')                        
        else:
            response, new_code = self._http_responses[str(status_code)](raw_response, status_code)
            return (response, new_code)

    def _default_response(self, json_response, status_code):
        return (json_response, status_code)

    def _translate(self, field, dict, value):        
        dict[field] = dict[field].format(value)

