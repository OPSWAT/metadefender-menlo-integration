

import json
import logging
import urllib.parse

import httpx

from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI


class MetaDefenderCloudAPI(MetaDefenderAPI):
    """MetaDefenderCloudAPI
    """

    def __init__(self, settings, url, apikey):
        self.service_name = SERVICE.MetaDefenderCloud
        self.settings = settings
        self.server_url = url
        self.apikey = apikey
        self.report_url = "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"

    def _get_submit_file_headers(self, filename, metadata):
        headers = {
            "Content-Type": "application/octet-stream",
            "rule": self.settings['scanRule']
        }

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
            return json_response['sanitized']['file_path']
        except Exception:
            return ''

    def check_analysis_complete(self, json_response):
        if ("sanitized" in json_response and "progress_percentage" in json_response["sanitized"]):
            return json_response["sanitized"]["progress_percentage"] == 100
        else:
            print(f"Unexpected response from MetaDefender: {json_response}")
            return False

    async def retrieve_sanitized_file(self, data_id, apikey, ip=""):

        response, http_status = await self._request_as_json_status(
            "sanitized_file",
            fields={
                "data_id": data_id
            },
            headers={
                'apikey': apikey,
                'x-forwarded-for': ip,
                'x-real-ip': ip
            }
        )

        self._log_response(response, http_status)

        if http_status == 401:
            return self._handle_unauthorized(response, http_status)

        fileurl = response.get("sanitizedFilePath", "")
        if fileurl:
            return await self._download_sanitized_file(fileurl, apikey)
        
        return await self._handle_no_sanitized_file(data_id, apikey)

    def _log_response(self, response, http_status):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "response": f"{response}", "status": f"{http_status}"
        }))

    def _handle_unauthorized(self, response, http_status):
        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
            "message": "Unauthorized request", "status": http_status
        }))
        return response, http_status

    async def _download_sanitized_file(self, fileurl, apikey):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "message": f"Download Sanitized file from {fileurl}"
        }))

        try:
            async with httpx.AsyncClient() as client:
                headers = {"User-Agent": "MenloTornadoIntegration"}
                response = await client.get(fileurl, headers=headers, timeout=300)
                return response.content, response.status_code
        except Exception as error:
            return self._handle_error(error, apikey)

    async def _handle_no_sanitized_file(self, data_id, apikey):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.server_url + f'/file/{data_id}', headers={'apikey': apikey}, timeout=300)
            
            sanitized_data = self._parse_sanitized_data(response)
            failure_reasons = self._get_failure_reasons(sanitized_data)
            
            return self._log_sanitization_result(failure_reasons)
        except Exception as error:
            return self._handle_error(error, apikey)

    def _parse_sanitized_data(self, response):
        response_data = json.loads(response.content.decode('utf-8'))
        return response_data.get("sanitized", {})

    def _get_failure_reasons(self, sanitized_data):
        return sanitized_data.get("failure_reasons") or sanitized_data.get("reason", "")

    def _log_sanitization_result(self, failure_reasons):
        http_status = 204
        if failure_reasons:
            logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Sanitization failed with failure reasons.",
                "failure_reasons": failure_reasons,
                "status": http_status
            }))
        else:
            logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                "message": "Sanitized file not available!", "status": http_status
            }))
        return "", http_status

    def _handle_error(self, error, apikey):
        logging.error("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin,
            TYPE.Internal,
            repr(error)
        ), {'apikey': apikey})
        return {"error": str(error)}, 500
