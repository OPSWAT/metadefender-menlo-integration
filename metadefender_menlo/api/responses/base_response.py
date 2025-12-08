
class BaseResponse(object):

    _allowed_responses = []
    _http_responses = {}

    def __init__(self, apikey='', allowed_responses=None):
        self._allowed_responses = allowed_responses
        self._apikey = apikey

        for code in allowed_responses:
            status_code = str(code)
            self._http_responses[status_code] = self._default_response

    async def handle_response(self, raw_response, status_code):
        int_status_code = int(status_code)
        if int_status_code not in self._allowed_responses:
            raise ValueError('Not Allowed: {0} response code not allowed'.format(status_code))

        str_status_code = str(status_code)
        response_body, new_code = await self._http_responses[str_status_code](raw_response, status_code)
        return (response_body, new_code)
        

    async def _default_response(self, json_response, status_code=200):
        return (json_response, status_code)

    def _translate(self, field, translation, value):
        translation[field] = translation[field].format(value)
