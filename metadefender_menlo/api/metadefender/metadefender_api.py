# import requests
from tornado.httpclient import AsyncHTTPClient
from tornado.httpclient import HTTPClientError
from abc import ABC, abstractmethod
import datetime
import os
import json
import logging


class MetaDefenderAPI(ABC):
    apikey = None
    server_url = 'http://localhost:8008'
    md_cls = lambda url, key: None
    report_url = ""
    
    api_endpoints = {
        "submit_file": {
            "type": "POST",
            "endpoint": "/file"
        },
        "retrieve_result": {
            "type": "GET",
            "endpoint": "/file/{data_id}"
        },
        "sanitized_file": {
            "type": "GET",
            "endpoint": "/file/converted/{data_id}"
        }, 
        "hash_lookup": {
            "type": "GET", 
            "endpoint": "/hash/{hash}"
        },
        
    }
    @staticmethod
    def config(url, apikey, metadefender_cls):
        MetaDefenderAPI.server_url = url
        MetaDefenderAPI.apikey = apikey
        MetaDefenderAPI.md_cls = metadefender_cls

    @staticmethod
    def get_instance():
        cls_func= MetaDefenderAPI.md_cls
        return cls_func(MetaDefenderAPI.server_url, MetaDefenderAPI.apikey)

    @abstractmethod
    def __init__(self, url, apikey):
        pass

    @abstractmethod
    def _get_submit_file_headers(self, filename, metadata):
        pass
    
    @abstractmethod
    def check_analysis_complete(self, json_response):
        pass
    
    async def submit_file(self, filename, fp, analysis_callback_url=None, metadata=None,apikey=""):  
        logging.info("Submit file > filename: {0} ".format(filename))   
    
        headers = self._get_submit_file_headers(filename, metadata)
        json_response, http_status = await self._request_as_json_status("submit_file", fields={'apikey':apikey}, body=fp, headers=headers)

        return (json_response, http_status)

    async def retrieve_result(self, data_id,apikey):
        logging.info("MetaDefender > Retrieve result for {0}".format(data_id))
        
        analysis_completed = False
        
        while (not analysis_completed):            
            json_response, http_status = await self.check_result(data_id,apikey)
            analysis_completed = self._check_analysis_complete(json_response)            
        
        return (json_response, http_status)

    async def check_result(self, data_id,apikey):
        logging.info("MetaDefender > Check result for {0}".format(data_id))        
        return await self._request_as_json_status("retrieve_result", fields={"data_id": data_id,'apikey':apikey})
    
    async def hash_lookup(self, sha256,apikey):
        logging.info("MetaDefender > Hash Lookup for {0}".format(sha256))    
        return await self._request_as_json_status("hash_lookup", fields={"hash": sha256,'apikey':apikey})
    
    @abstractmethod
    async def retrieve_sanitized_file(self, data_id,apikey):        
        pass

    async def _request_as_json_status(self, endpoint_id, fields=None, headers=None, body=None):
        response, http_status = await self._request_status(endpoint_id, fields, headers, body)

        json_resp = json.loads(response)

        return (json_resp, http_status)

    async def _request_status(self, endpoint_id, fields=None, headers=None, body=None):

        logging.info("MetaDefender Request > ({0}) for {1}".format(endpoint_id, fields))   

        endpoint_details = self.api_endpoints[endpoint_id]
        endpoint_path = endpoint_details["endpoint"]
        if fields is not None:
            endpoint_path = endpoint_details["endpoint"].format(**fields)
        metadefender_url = self.server_url + endpoint_path
        request_method = endpoint_details["type"]
        
        if fields["apikey"] is not None: 
            if not headers:
                headers = {}
            logging.debug("Add apikey: {0}".format(fields["apikey"]))
            headers["apikey"] = fields["apikey"]
        before_submission = datetime.datetime.now()        
        logging.info("Request [{0}]: {1}".format(request_method, metadefender_url))
        http_status = None
        response_body = None
        http_client = AsyncHTTPClient(None, defaults=dict(user_agent="MenloTornadoIntegration", validate_cert=False))
        try:
            response = await http_client.fetch(request=metadefender_url, method=request_method, headers=headers, body=body)
            http_status = response.code
            response_body = response.body
        except HTTPClientError as error:
            http_status = error.code
            response_body = '{"error": "' + error.message + '"}'
        except Exception as e:
            http_status = 500
            response_body = '{"error": "' + e.strerror + '"}'
                            
        total_submission_time = datetime.datetime.now() - before_submission

        logging.info("{timestamp} {name} >> time: {total_time}, http status: {status}".format(timestamp=before_submission, name=endpoint_id, total_time=total_submission_time, status=http_status))                

        return (response_body, http_status)