from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.responses.base_response import BaseResponse
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse
import logging
from metadefender_menlo.api.log_types import SERVICE, TYPE


class FileAnalyis(BaseResponse):

    def __init__(self, allowedResponses=None):

        allowedResponses = [200, 400, 401, 404, 500]
        super().__init__(allowedResponses)

        self._http_responses["200"] = self.__response200
        self._http_responses["400"] = self.__response400
        self._http_responses["401"] = self.__response400
        self._http_responses["404"] = self.__response400

    def model_outcome(self, result, json_response):
        if result == 'completed':
            if json_response['process_info']['profile'] == 'cdr':
                return 'unknown' if ("sanitized" in json_response
                                     and "result" in json_response["sanitized"]
                                     and json_response['sanitized']['result'] != 'Allowed'
                                     ) else 'clean'
            return 'clean' if json_response['process_info']['result'] == 'Allowed' else 'infected'
        else:
            return 'unknown'

    def check_analysis_complete(self, json_response):
        scan_progress = 0 if not (
            "process_info" in json_response and "progress_percentage" in json_response["process_info"]) else json_response["process_info"]["progress_percentage"]
        sanitized_progress = 100 if not (
            "sanitized" in json_response and "progress_percentage" in json_response["sanitized"]) else json_response["sanitized"]["progress_percentage"]

        return scan_progress == 100 and sanitized_progress == 100

    def __response200(self, json_response, status_code):
        try:
            if 'data_id' not in json_response:
                return (json_response, 404)

            model = FileAnalysisResponse()
            analysis_completed = self.check_analysis_complete(json_response)

            model.result = 'pending' if not analysis_completed else 'completed'
            model.outcome = self.model_outcome(model.result, json_response)
            model.report_url = MetaDefenderAPI.get_instance(
            ).report_url.format(data_id=json_response['data_id'])
            model.filename = json_response['file_info']['display_name'].encode('latin1').decode('unicode-escape')

            if model.outcome == 'unknown':
                model.modifications = []
                return (model.to_dict(), 200)

            post_process = json_response['process_info']['post_processing']
            if 'sanitization_details' in post_process:
                if 'details' in post_process['sanitization_details']:
                    details = post_process['sanitization_details']['details']
                    modifications = []

                    if (isinstance(details, list)):
                        for item in details:
                            action = item['action'] if 'action' in item else 'Undefined Action'
                            count = item['count'] if 'count' in item else 'All'
                            obj_name = item['object_name'] if 'object_name' in item else 'All'
                            modifications.append(
                                "Action: {0} - Count: {1} - Object type: {2}".format(action, count, obj_name))
                    else:
                        modifications = [details]

                    model.modifications = modifications

            return (model.to_dict(), 200)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error), "MdCloudResponse": json_response
            }))
            return ({}, 500)

    def __response400(self, json_response, status_code):
        return ({}, status_code)
