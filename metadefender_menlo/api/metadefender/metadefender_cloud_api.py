from tornado.httpclient import AsyncHTTPClient
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
import json
import logging


class MetaDefenderCloudAPI(MetaDefenderAPI):
    
    def __init__(self, url, apikey):
        self.server_url = url
        self.apikey = apikey
        self.report_url = "https://metadefender.opswat.com/results/file/{data_id}/regular/overview"
    
    def _get_submit_file_headers(self, filename, metadata):    
        headers = {
            "filename": filename, 
            "Content-Type": "application/octet-stream", 
            "rule": "multiscan,sanitize,unarchive"
        }
        logging.debug("Add headers: {0}".format(headers))
        return headers
    
    def check_analysis_complete(self, json_response):
        if ("sanitized" in json_response and "progress_percentage" in json_response["sanitized"]):
            return json_response["sanitized"]["progress_percentage"] == 100
        else:
            print("Unexpected response from MetaDefender: {0}".format(json_response))
            return False
        
    async def retrieve_sanitized_file(self, data_id, apikey, ip):        
        logging.info("MetaDefender > Retrieve Sanitized file for {0}".format(data_id))
        response, http_status = await self._request_as_json_status("sanitized_file", fields={"data_id": data_id}, headers={'apikey':apikey, 'x-forwarded-for': ip, 'x-real-ip': ip})

        if "sanitizedFilePath" in response:
            fileurl = response["sanitizedFilePath"]
            logging.info("Download Sanitized file from {path}".format(path=fileurl))
            
            http_client = AsyncHTTPClient(None, defaults=dict(user_agent="MetaDefenderMenloMiddleware", validate_cert=False))
            response = await http_client.fetch(request=fileurl, method="GET")
            http_status = response.code            
            return (response.body, http_status)
        else:
            logging.info("Sanitized file not available!")
        return (response, http_status)
