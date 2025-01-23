
import logging
import urllib.parse

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse
from metadefender_menlo.api.responses.base_response import BaseResponse


class FileAnalyis(BaseResponse):

    def __init__(self, apikey='', allowedResponses=None):
        
        allowedResponses = [200, 400, 401, 404, 500]
        super().__init__(apikey, allowedResponses)

        self._http_responses["200"] = self.__response200
        self._http_responses["400"] = self.__response400
        self._http_responses["401"] = self.__response401
        self._http_responses["404"] = self.__response400

    def model_outcome(self, result, json_response):
        if result != 'completed' :
            return 'unknown'

        process_info = json_response.get('process_info', {})
        profile = process_info.get('profile', '')

        if profile == 'cdr' or 'sanitize' in profile:
            sanitized_info = json_response.get('sanitized', {})
            sanitized_result = sanitized_info.get('result')
            
            if sanitized_result == 'Allowed':
                return 'clean'
            if sanitized_result == 'Error':
                return 'error'
            if sanitized_result == 'unknown':
                return 'unknown'
            
        return 'clean' if process_info.get('result') == 'Allowed' else 'infected'
       

    def check_analysis_complete(self, json_response):
        scan_progress = 0 if not (
            "process_info" in json_response and "progress_percentage" in json_response["process_info"]) else json_response["process_info"]["progress_percentage"]
        sanitized_progress = 100 if not (
            "sanitized" in json_response and "progress_percentage" in json_response["sanitized"]) else json_response["sanitized"]["progress_percentage"]
    
        return scan_progress == 100 and sanitized_progress == 100
    
    def __response200(self, json_response, _status_code):
        try:
            if 'data_id' not in json_response: 
                return (json_response, 404)

            model = self._initialize_model(json_response)

            if model.outcome == 'unknown':
                model.modifications = []
                return (model.to_dict(), 200) 

            post_process = json_response['process_info']['post_processing']
            self._update_sanitization_details(model, post_process)

            return (model.to_dict(), 200)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error), "MdCloudResponse": json_response
            }), {'apikey': self._apikey})
            return ({}, 500)

    def __response400(self, _json_response, status_code):
        return ({}, status_code)

    def __response401(self, response, status_code):
        return ({}, 401)
    

    def _initialize_model(self, json_response):
        model = FileAnalysisResponse()
        analysis_completed = self.check_analysis_complete(json_response)
        
        model.result = 'pending' if not analysis_completed else 'completed'
        model.outcome = self.model_outcome(model.result, json_response)
        model.report_url = MetaDefenderAPI.get_instance().report_url.format(data_id=json_response['data_id'])
        
        model.filename = self._extract_filename(json_response)
        return model
    
    def _extract_filename(self, json_response):
        try:
            return urllib.parse.unquote(json_response['file_info']['display_name'])
        except Exception:
            return ""

    def _update_sanitization_details(self, model, post_process):
        sanitization_details = post_process.get('sanitization_details', {})
        details = sanitization_details.get('details', [])
        
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