
from abc import ABC, abstractmethod
import ast
import datetime
import json
import logging
import httpx
from tornado.httpclient import HTTPClientError
from metadefender_menlo.api.log_types import SERVICE, TYPE


class MetaDefenderAPI(ABC):
    service_name = SERVICE.MetaDefenderAPI
    settings = None
    apikey = None
    server_url = 'http://localhost:8008'
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
        }
    }
    def md_cls(self, url, key): return None

    @staticmethod
    def config(settings, url, apikey, metadefender_cls):
        MetaDefenderAPI.settings = settings
        MetaDefenderAPI.server_url = url
        MetaDefenderAPI.apikey = apikey
        MetaDefenderAPI.md_cls = metadefender_cls

    @staticmethod
    def get_instance():
        cls_func = MetaDefenderAPI.md_cls
        return cls_func(MetaDefenderAPI.settings, MetaDefenderAPI.server_url, MetaDefenderAPI.apikey)

    @abstractmethod
    def __init__(self, url, apikey):
        pass

    @abstractmethod
    def _get_submit_file_headers(self, filename, metadata):
        pass

    @abstractmethod
    def check_analysis_complete(self, json_response):
        pass

    @abstractmethod
    def get_sanitized_file_path(self, json_response):
        pass

    def _get_decoded_parameter(self, param_str):
        if param_str:
            param_list = ast.literal_eval(param_str) 
            param = param_list[0].decode('utf-8') if param_list else None
        else:
            param = None 
        return param

    async def submit_file(self, filename, fp, metadata=None, apikey="", ip=None):

        headers = self._get_submit_file_headers(filename, metadata)
        headers = {
            **headers, 
            **{'apikey': apikey},
            'x-forwarded-for': ip, 
            'x-real-ip': ip
        }
        json_response, http_status = await self._request_as_json_status("submit_file", body=fp, headers=headers)

        return (json_response, http_status)

    async def retrieve_result(self, data_id, apikey):
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "message": f"Retrieve result for {data_id}"
        }))

        analysis_completed = False

        while (not analysis_completed):
            json_response, http_status = await self.check_result(data_id, apikey)
            analysis_completed = self._check_analysis_complete(json_response)

        return (json_response, http_status)

    async def check_result(self, data_id, apikey, ip):
        return await self._request_as_json_status("retrieve_result", fields={"data_id": data_id}, headers={'apikey': apikey, 'x-forwarded-for': ip, 'x-real-ip': ip})

    async def hash_lookup(self, sha256, apikey, ip):
        logging.info("{0} > {1} > {2}".format(
            self.service_name, TYPE.Request, {"message": "Hash Lookup for {0}".format(sha256)}))
        return await self._request_as_json_status("hash_lookup", fields={"hash": sha256}, headers={'apikey': apikey, 'x-forwarded-for': ip, 'x-real-ip': ip})

    @abstractmethod
    async def retrieve_sanitized_file(self, data_id, apikey, ip):
        pass

    async def _request_as_json_status(self, endpoint_id, fields=None, headers=None, body=None):
        response, http_status = await self._request_status(endpoint_id, fields, headers, body)

        json_resp = json.loads(response)

        return (json_resp, http_status)

    async def _request_status(self, endpoint_id, fields=None, headers=None, body=None):

        endpoint_details = self.api_endpoints[endpoint_id]
        endpoint_path = endpoint_details["endpoint"]
        if fields is not None:
            endpoint_path = endpoint_details["endpoint"].format(**fields)
        metadefender_url = self.server_url + endpoint_path

        request_method = endpoint_details["type"]

        if headers and self.apikey and headers["apikey"] is None:
            headers["apikey"] = self.apikey

        before_submission = datetime.datetime.now()
        logging.info("{0} > {1} >{2}".format(self.service_name, TYPE.Request, {
            "request_method": request_method,
            "endpoint": metadefender_url,
            "apikey": headers["apikey"]
        }))

        http_status = None
        response_body = None

        headers["User-Agent"] = "MenloTornadoIntegration"
        try:
            async with httpx.AsyncClient() as client:
                response: httpx.Response = await client.request(request_method, metadefender_url, headers=headers, timeout=60, content=body)
                http_status = response.status_code
                response_body = response.content

            total_submission_time = datetime.datetime.now() - before_submission

            logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "request_time": total_submission_time.total_seconds(),
                "http_status": http_status
            }))
        except HTTPClientError as error:
            # TODO: When is it raised (It is not raised on 4xx or 5xx from client.request)
            http_status = error.code
            response_body = reponse_body_error(error)
        except OSError as error:
            logging.error("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "OSError: ": repr(error)
            }), {'apikey': self.apikey})
            http_status = 500
            response_body = reponse_body_error(error)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "Exception: ": repr(error)
            }),  {'apikey': self.apikey})
            http_status = 500
            response_body = reponse_body_error(error)

        return (response_body, http_status)
    
    async def get_sanitized_file_headers(self, data_id, apikey):
        """
        Get only the headers for a sanitized file without downloading the content
        """
        url = self.server_url + self.api_endpoints["sanitized_file"]["endpoint"].format(data_id=data_id)
        
        headers = {
            "apikey": apikey,
            "User-Agent": "MenloTornadoIntegration",
            "Range": "bytes=0-0"
        }

        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", url, headers=headers, timeout=3) as response:
                    headers_received = response.headers
                    await response.aclose()
                    return headers_received
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "Exception: ": repr(error)
            }),  {'apikey': self.apikey})
            return None


def reponse_body_error(message):
    return '{"error": "' + str(message) + '"}'
