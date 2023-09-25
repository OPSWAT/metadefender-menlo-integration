
import logging
from os import environ
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.log_types import SERVICE, TYPE
import httpx

class MetaDefenderCloudAPI(MetaDefenderAPI):
    """MetaDefenderCloudAPI
    """

    settings = None

    def __init__(self, config, url, apikey):
        self.settings = config
        self.server_url = url
        self.apikey = apikey
        self.report_url = "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"

    def _get_submit_file_headers(self, filename, metadata):
        headers = {
            "filename": filename.encode('unicode-escape').decode('latin1'),
            "Content-Type": "application/octet-stream",
            "rule": self.settings['scanRule']
        }
        logging.debug("{0} > {1} > {2} Add headers: {0}".format(
            SERVICE.MenloPlugin, TYPE.Internal, {"apikey": self.apikey}))
        return headers

    def check_analysis_complete(self, json_response):
        if ("sanitized" in json_response and "progress_percentage" in json_response["sanitized"]):
            return json_response["sanitized"]["progress_percentage"] == 100
        else:
            print(f"Unexpected response from MetaDefender: {json_response}")
            return False

    async def retrieve_sanitized_file(self, data_id, apikey, ip):

        response, http_status = await self._request_as_json_status(
            "sanitized_file",
            fields={
                "data_id": data_id
            },
            headers={
                'apikey': apikey,
                'x-forwarded-for': ip,
                'x-real-ip': ip
            })

        logging.info("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
            "response": f"{response}", "status": f"{http_status}"
        }))

        try:
            fileurl = ""
            if "sanitizedFilePath" in response:
                fileurl = response["sanitizedFilePath"]
            if http_status == 401:
                logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                    "message": " Unauthorized request", "status": http_status
                }))
                return (response, http_status)
            if fileurl != "":
                logging.info("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                    "message": f"Download Sanitized file from {fileurl}"
                }))

                try:

                    async with httpx.AsyncClient() as client:
                        headers = {"User-Agent": "MenloTornadoIntegration"}
                        response:httpx.Response = await client.get(fileurl, headers=headers, timeout=300)

                        http_status = response.status_code
                        return (response.content, http_status)
                except Exception as error:
                    logging.error("{0} > {1} > {2}".format(
                        SERVICE.MenloPlugin,
                        TYPE.Internal,
                        repr(error)
                    ))
                    return ({"error": str(error)}, 500)
            else:
                http_status = 204
                logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Response, {
                    "message": "Sanitized file not available!", "status": http_status
                }))
                return ("", http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(SERVICE.MetaDefenderCloud, TYPE.Response, {
                "error": repr(error), "MdCloudResponse": response
            }))
            return ({}, 500)
