import json
import logging
import urllib.parse

from httpx import AsyncClient
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.utils.http_client_manager import HttpClientManager

class MetaDefenderCoreAPI(MetaDefenderAPI):

    def __init__(self, settings, url, apikey):
        super().__init__(settings, url, apikey)
        self.service_name = SERVICE.meta_defender_core
        self.settings = settings
        self.server_url = url
        self.apikey = apikey
        self.report_url = self.server_url + "/#/public/process/dataId/{data_id}"
        self.api_endpoints = {
            "file_submit": {"method": "POST", "endpoint": "/file"},
            "check_result": {"method": "GET", "endpoint": "/file/{data_id}"},
            "hash_lookup": {"method": "GET", "endpoint": "/hash/{hash}"},
            "sanitized_file": {"method": "GET", "endpoint": "/file/converted/{data_id}"},
            "health_check": {"method": "GET", "endpoint": "/admin/config/healthcheck"}
        }

    async def check_hash(self, sha256, apikey, client_ip):
        json_response, http_status = await super().check_hash(sha256, apikey, client_ip)
        if any(value == "Not Found" for value in json_response.values()):
            return {"sha256": sha256}, 404
        return json_response, http_status

    async def check_core_health(self, apikey):
        header = {'apikey': apikey}
        url = self.server_url + self.api_endpoints["health_check"]["endpoint"]
        headers = self._add_scan_with_header(header)
        json_response, http_status = await self._request_core_health_as_json(url, "GET", headers=headers)
        return json_response, http_status

    def _get_submit_file_headers(self, metadata, apikey, client_ip):

        content_length = str(metadata.get('content-length', 0))
        if 'content-length' in metadata:
            del metadata['content-length']

        headers = {
            "Content-Type": "application/octet-stream",
            "Content-Length": content_length,
            "metadata": json.dumps(metadata) if metadata is not None else "",
            "engines-metadata": self.settings['headers_engines_metadata'],
            "apikey": apikey,
        }

        if client_ip:
            headers['x-forwarded-for'] = client_ip
            headers['x-real-ip'] = client_ip

        if self.settings['scanRule']:
            headers["rule"] = self.settings['scanRule']
        
        file_name = self._get_decoded_parameter(metadata.get('filename'))
        if file_name:
            headers["filename"] = urllib.parse.quote(file_name)

        headers = {k: v for k, v in headers.items() if v is not None}

        logging.debug("{0} > {1} > {2} Add headers: {0}".format(
            SERVICE.menlo_plugin, TYPE.internal, {"apikey": self.apikey}))
        
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

    async def sanitized_file(self, data_id, apikey, ip=""):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.response, {
            "message": f"Retrieve Sanitized file for {data_id}"
        }))
        
        upstream_url = self._get_url("sanitized_file", {"data_id": data_id})

        headers = {
            'apikey': apikey,
            'x-forwarded-for': ip,
            'x-real-ip': ip,
            'User-Agent': 'MenloTornadoIntegration'
        }

        client: AsyncClient = HttpClientManager.get_client()
        req = client.build_request("GET", upstream_url, headers=headers)
        resp = await client.send(req, stream=True)

        http_status = resp.status_code
        if http_status == 404 and self.settings['fallbackToOriginal']:
            http_status = 204

        return (resp, http_status, client)

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
