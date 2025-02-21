
import json
import logging
import urllib.parse

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI


class MetaDefenderCoreAPI(MetaDefenderAPI):

    def __init__(self, settings, url, apikey):
        self.service_name = SERVICE.MetaDefenderCore
        self.settings = settings
        self.server_url = url
        self.apikey = apikey
        self.report_url = self.server_url + "/#/public/process/dataId/{data_id}"

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

    def check_analysis_complete(self, json_response):
        if ("process_info" in json_response and "progress_percentage" in json_response["process_info"]):
            return json_response["process_info"]["progress_percentage"] == 100
        else:
            print(f"Unexpected response from MetaDefender: {json_response}")
            return False

    async def retrieve_sanitized_file(self, data_id, apikey, ip):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "message": f"Retrieve Sanitized file for {data_id}"
        }))
        response, http_status = await self._request_status("sanitized_file", fields={"data_id": data_id}, headers={"apikey": apikey})

        if http_status == 404 and self.settings['fallbackToOriginal']:
            http_status = 204
            response = ""

        return (response, http_status)
