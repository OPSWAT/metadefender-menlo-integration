
import re
import logging
import urllib.parse

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse
from metadefender_menlo.api.responses.base_response import BaseResponse


class FileAnalyis(BaseResponse):

    def __init__(self, apikey=''):
        super().__init__(apikey, [200, 400, 401, 404, 500])

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
    
    async def __response200(self, json_response, _status_code):
        try:
            if 'data_id' not in json_response: 
                return (json_response, 404)

            model = await self._initialize_model(json_response)

            if model.outcome == 'unknown':
                model.modifications = []
                return (model.to_dict(), 200) 

            post_process = json_response['process_info']['post_processing']
            self._update_sanitization_details(model, post_process)

            return (model.to_dict(), 200)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.meta_defender_api, TYPE.response, {
                "error": repr(error), "MdCloudResponse": json_response
            }), {'apikey': self._apikey})
            return ({}, 500)

    async def __response400(self, _json_response, status_code):
        return ({}, status_code)

    async def __response401(self, response, status_code):
        return ({}, 401)
    

    async def _initialize_model(self, json_response):
        md_instance = MetaDefenderAPI.get_instance()
        analysis_completed = self.check_analysis_complete(json_response)

        model = FileAnalysisResponse()
        model.result = 'pending' if not analysis_completed else 'completed'
        model.outcome = self.model_outcome(model.result, json_response)
        model.report_url = md_instance.report_url.format(data_id=json_response['data_id'])
        model.filename = await self._extract_filename(json_response)
        try:
            model.sanitized_file_path = md_instance.get_sanitized_file_path(json_response)
        except Exception:
            pass
        
        return model
    
    async def _extract_filename_from_headers(self, response_headers):
        filename = None
        try:
            content_disposition = response_headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                match = re.search(r'filename="([^"]+)"', content_disposition)
                if match:
                    filename = match.group(1)
                    # URL-decode the filename to handle percent-encoded characters
                    filename = urllib.parse.unquote(filename)
                else:
                    # Fallback to the old method if regex doesn't match
                    filename = content_disposition.split("filename=")[-1].strip('"')
        except Exception as _error:
            pass
            
        return filename
    
    async def _extract_filename(self, json_response):
        try:
            md_instance = MetaDefenderAPI.get_instance()
            haders = await md_instance.get_sanitized_file_headers(json_response['data_id'], self._apikey)
            filename = await self._extract_filename_from_headers(haders)
            if filename:
                return filename
            
            display_name = urllib.parse.unquote(json_response['file_info']['display_name'])

            try:
                # Check if 'result' exists inside 'sanitized'
                if json_response.get('sanitized', {}).get('result') == 'Allowed' or "Sanitized" in json_response['process_info']['post_processing']['actions_ran']:
                    display_name = "sanitized_{display_name}".format(display_name=display_name)
            except Exception:
                pass

            return display_name
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