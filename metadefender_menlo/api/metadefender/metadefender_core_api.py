import json
import logging
import urllib.parse

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI


class MetaDefenderCoreAPI(MetaDefenderAPI):

    def __init__(self, settings, url, apikey):
        super().__init__(settings, url, apikey)
        self.service_name = SERVICE.MetaDefenderCore
        self.settings = settings
        self.server_url = url
        self.apikey = apikey
        self.report_url = self.server_url + "/#/public/process/dataId/{data_id}"
        self.api_endpoints = {
            "file_submit": {"method": "POST", "endpoint": "/file"},
            "check_result": {"method": "GET", "endpoint": "/file/{data_id}"},
            "hash_lookup": {"method": "GET", "endpoint": "/hash/{hash}"},
            "sanitized_file": {"method": "GET", "endpoint": "/file/converted/{data_id}"}
        }

    def _get_submit_file_headers(self, filename, metadata):
        headers = {
            "Content-Type": "application/octet-stream",
            "metadata": json.dumps(metadata) if metadata is not None else "",
            "engines-metadata": self.settings['headers_engines_metadata']
        }

        if self.settings['scanRule']:
            headers["rule"] = self.settings['scanRule']
        
        file_name = self._get_decoded_parameter(metadata.get('fileName'))
        if file_name or filename:
            headers["filename"] = urllib.parse.quote(file_name if file_name is not None else filename)

        downloadfrom = self._get_decoded_parameter(metadata.get('downloadfrom'))
        if downloadfrom:
            headers["downloadfrom"] = downloadfrom

        logging.debug("{0} > {1} > {2} Add headers: {0}".format(
            SERVICE.MenloPlugin, TYPE.Internal, {"apikey": self.apikey}))
        
        return headers
    
    def get_sanitized_file_path(self, json_response):
        try:
            if "Sanitized" in json_response['process_info']['post_processing']['actions_ran']:
                data_id = json_response['data_id']
                return f"{self.server_url}/file/converted/{data_id}"
        except Exception:
            return ''
        return ''

    def check_analysis_complete(self, json_response):
        if ("process_info" in json_response and "progress_percentage" in json_response["process_info"]):
            return json_response["process_info"]["progress_percentage"] == 100
        else:
            logging.error(f"Unexpected response from MetaDefender: {json_response}")
            return False

    async def retrieve_sanitized_file(self, data_id, apikey, ip=""):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "message": f"Retrieve Sanitized file for {data_id}"
        }))
        
        response, http_status = await self._request_status(
            "sanitized_file", 
            fields={"data_id": data_id}, 
            headers={"apikey": apikey}
        )

        if http_status == 404 and self.settings['fallbackToOriginal']:
            http_status = 204
            response = b""

        return (response, http_status)

    async def _extract_filename_from_headers(self, response_headers):
        filename = None
        try:
            content_disposition = response_headers.get("content-disposition", "")
            if "filename=" in content_disposition:
                # Extract the content between the first set of double quotes after "filename="
                import re
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
