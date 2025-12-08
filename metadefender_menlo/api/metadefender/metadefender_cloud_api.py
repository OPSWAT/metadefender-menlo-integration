import logging
import urllib.parse
from httpx import AsyncClient

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.utils.http_client_manager import HttpClientManager

class MetaDefenderCloudAPI(MetaDefenderAPI):
    """MetaDefenderCloudAPI implementation for aiohttp
    """

    def __init__(self, settings, url, apikey):
        super().__init__(settings, url, apikey)
        self.service_name = SERVICE.meta_defender_cloud
        self.settings = settings
        self.server_url = url
        self.apikey = apikey
        self.report_url = "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"

    def _get_submit_file_headers(self, metadata, apikey, client_ip):
        
        headers = {
            **metadata,
            "Content-Type": "application/octet-stream",
            "rule": self.settings['scanRule'],
            "apikey": apikey,
        }

        if client_ip:
            headers['x-forwarded-for'] = client_ip
            headers['x-real-ip'] = client_ip

        file_name = self._get_decoded_parameter(metadata['filename'])
        headers["filename"] = urllib.parse.quote(file_name)

        headers = {k: v for k, v in headers.items() if v is not None}
        headers = self._add_scan_with_header(headers)
        
        logging.debug("{0} > {1} > Add headers: {2}".format(
            SERVICE.menlo_plugin, TYPE.internal, headers))
        
        return headers
    
    def get_sanitized_file_path(self, json_response):
        try:
            return json_response['sanitized']['file_path']
        except Exception:
            return ''

    def check_analysis_complete(self, json_response):
        if ("sanitized" in json_response and "progress_percentage" in json_response["sanitized"]):
            return json_response["sanitized"]["progress_percentage"] == 100
        else:
            print(f"Unexpected response from MetaDefender: {json_response}")
            return False

    async def sanitized_file(self, data_id, apikey, ip=""):
        headers = {
            'apikey': apikey,
            'x-forwarded-for': ip,
            'x-real-ip': ip
        }
        headers = self._add_scan_with_header(headers)
        
        response, http_status = await self._request_as_json_status(
            "sanitized_file",
            fields={
                "data_id": data_id
            },
            headers=headers
        )

        if http_status == 401:
            return response, http_status, None

        upstream_url = response.get("sanitizedFilePath", "")
        if upstream_url:
            client: AsyncClient = HttpClientManager.get_client()
            req = client.build_request("GET", upstream_url)
            resp = await client.send(req, stream=True)

            http_status = resp.status_code
            if http_status == 404 and self.settings['fallbackToOriginal']:
                http_status = 204

            return resp, http_status, client
        
        return await self._handle_no_sanitized_file(data_id, apikey)

    async def _download_sanitized_file(self, fileurl, apikey):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.response, {
            "message": f"Download Sanitized file from {fileurl}"
        }))

        try:
            client: AsyncClient = HttpClientManager.get_client()
            headers = {"User-Agent": "MenloTornadoIntegration"}
            response = await client.get(fileurl, headers=headers)
            content = response.content
            return content, response.status_code
        except Exception as error:
            return self._handle_error(error, apikey)

    async def _handle_no_sanitized_file(self, data_id, apikey):
        try:
            client: AsyncClient = HttpClientManager.get_client()
            headers = {'apikey': apikey}
            headers = self._add_scan_with_header(headers)
            response = await client.get(
                self.server_url + f'/file/{data_id}', 
                headers=headers
            )

            response_content = response.json()
            sanitized_data = response_content.get("sanitized", {})
            failure_reasons = sanitized_data.get("failure_reasons") or sanitized_data.get("reason", "")
            
            return self._log_sanitization_result(failure_reasons)
        except Exception as error:
            return self._handle_error(error, apikey)

    def _log_sanitization_result(self, failure_reasons):
        http_status = 204
        if failure_reasons:
            logging.info("{0} > {1} > {2}".format(SERVICE.menlo_plugin, TYPE.response, {
                "message": "Sanitization failed with failure reasons.",
                "failure_reasons": failure_reasons,
                "status": http_status
            }))
        else:
            logging.info("{0} > {1} > {2}".format(SERVICE.menlo_plugin, TYPE.response, {
                "message": "Sanitized file not available!", "status": http_status
            }))
        return None, http_status, None

    def _handle_error(self, error, apikey):
        logging.error("{0} > {1} > {2}".format(
            SERVICE.menlo_plugin,
            TYPE.internal,
            repr(error)
        ), {'apikey': apikey})
        return {"error": str(error)}, 500
