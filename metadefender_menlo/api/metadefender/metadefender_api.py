
from abc import ABC, abstractmethod
import ast
import json
import urllib.parse
import logging
import aiohttp

from metadefender_menlo.api.log_types import SERVICE, TYPE


class MetaDefenderAPI(ABC):

    _instance = None

    
    def __init__(self, settings, server_url, apikey):
        self.service_name = SERVICE.MetaDefenderAPI
        self.settings = settings
        self.server_url = server_url
        self.apikey = apikey
        self.api_endpoints = {
            "file_submit": {"method": "POST", "endpoint": "/file"},
            "check_result": {"method": "GET", "endpoint": "/file/{data_id}"},
            "hash_lookup": {"method": "GET", "endpoint": "/hash/{hash}"},
            "sanitized_file": {"method": "GET", "endpoint": "/file/converted/{data_id}"}
        }

    @classmethod
    def config(cls, settings, server_url, apikey, md_cls=None):
        cls.settings = settings
        cls.server_url = server_url
        cls.apikey = apikey
        cls.md_cls = md_cls
        

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls.md_cls(cls.settings, cls.server_url, cls.apikey)
        return cls._instance
        
    async def get_sanitized_file_headers(self, data_id, apikey):
        """
        Get headers for a sanitized file by requesting just a small range
        to avoid downloading the entire file
        """
        url = self._get_url("sanitized_file", {"data_id": data_id})
        
        headers = {
            "apikey": apikey,
            "User-Agent": "MenloTornadoIntegration",
            "Range": "bytes=0-0"  # Request only first byte to minimize data transfer
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                # Use GET with Range header instead of HEAD
                response = await session.get(url, headers=headers)
                return response.headers
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "Exception: ": repr(error)
            }),  {'apikey': self.apikey})
            return {}  # Return empty dict instead of None

    async def submit_file(self, filename, file_bytes, apikey, metadata, ip=""):
        """Submit a file for scanning

        Args:
            filename: Original filename
            file_bytes: Bytes content of the file
            apikey: API key for authentication
            metadata: Additional metadata to send with the file
            ip: IP address of the client

        Returns:
            API response and status code
        """
        headers = self._get_submit_file_headers(filename, metadata)
        headers["apikey"] = apikey
        headers["x-forwarded-for"] = ip
        headers["x-real-ip"] = ip
        
        response, status = await self._request_as_json("submit_file", data=file_bytes, headers=headers)
        
        return response, status

    async def check_result(self, data_id, apikey, ip=""):
        """Check analysis result for a data_id

        Args:
            data_id: Data ID to check
            apikey: API key for authentication
            ip: IP address of the client

        Returns:
            API response and status code
        """
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Request, {
            "message": "Check result", "data_id": data_id
        }))
        
        headers = {
            'apikey': apikey,
            'x-forwarded-for': ip,
            'x-real-ip': ip
        }
        
        response, status = await self._request_as_json("check_result", fields={"data_id": data_id}, headers=headers)
        
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "status": status, "response": response
        }))
        
        return response, status

    async def check_hash(self, hash_value, apikey, ip=""):
        """Check if a file hash exists

        Args:
            hash_value: Hash value to check
            apikey: API key for authentication
            ip: IP address of the client

        Returns:
            API response and status code
        """
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Request, {
            "message": "Check hash", "hash": hash_value
        }))
        
        headers = {
            'apikey': apikey,
            'x-forwarded-for': ip,
            'x-real-ip': ip
        }
        
        response, status = await self._request_as_json("hash_lookup", fields={"hash": hash_value}, headers=headers)
        
        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
            "status": status, "response": response
        }))
        
        return response, status
    
    def _get_url(self, api_type, fields={}):
        """ Create the URL for an API request.

        Args:
            api_type: the API endpoint string type
            fields: dictionary to replace placeholders in endpoint URLs

        Returns:
            The complete URL as a string
        """
        api_data = self.api_endpoints[api_type]
        endpoint = api_data["endpoint"]
        
        # Replace placeholders in endpoint URL with provided values
        for key, value in fields.items():
            if isinstance(value, str):
                endpoint = endpoint.replace("{"+key+"}", value)

        return self.server_url + endpoint

    async def _request_as_json(self, api_type, fields={}, data=None, headers={}):
        """Make an API request and return the JSON response

        Args:
            api_type: the API endpoint string type
            fields: dictionary to replace placeholders in endpoint URLs
            data: payload to send with the request (for POST)
            headers: dictionary of headers to include

        Returns:
            JSON response object
        """
        url = self._get_url(api_type, fields)
        method = self.api_endpoints[api_type]["method"]
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                response = await session.get(url, headers=headers)
            elif method == "POST":
                response = await session.post(url, data=data, headers=headers)
            
            status_code = response.status
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                json_response = await response.json()
                return json_response, status_code
            else:
                text_response = await response.text()
                return text_response, status_code

    async def _request_as_bytes(self, api_type, fields={}, headers={}):
        """Make an API request and return the raw bytes response

        Args:
            api_type: the API endpoint string type
            fields: dictionary to replace placeholders in endpoint URLs
            headers: dictionary of headers to include

        Returns:
            bytes data and status code
        """
        url = self._get_url(api_type, fields)
        method = self.api_endpoints[api_type]["method"]
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                response = await session.get(url, headers=headers)
            
            status_code = response.status
            content = await response.read()
            return content, status_code

    async def _request_status(self, api_type, fields={}, data=None, headers={}):
        """Make an API request and handle binary response

        Args:
            api_type: the API endpoint string type
            fields: dictionary to replace placeholders in endpoint URLs
            data: payload to send with the request (for POST)
            headers: dictionary of headers to include

        Returns:
            Data and status code
        """
        url = self._get_url(api_type, fields)
        method = self.api_endpoints[api_type]["method"]
        
        async with aiohttp.ClientSession() as session:
            if method == "GET":
                response = await session.get(url, headers=headers)
            elif method == "POST":
                response = await session.post(url, data=data, headers=headers)
            
            status_code = response.status
            content = await response.read()
            return content, status_code

    async def _request_as_json_status(self, api_type, fields={}, data=None, headers={}):
        """Make an API request and handle both JSON and status code

        Args:
            api_type: the API endpoint string type
            fields: dictionary to replace placeholders in endpoint URLs
            data: payload to send with the request (for POST)
            headers: dictionary of headers to include

        Returns:
            JSON response object and status code
        """
        response, status_code = await self._request_as_json(api_type, fields, data, headers)
        return response, status_code

    def _get_decoded_parameter(self, param):
        """Decode URL parameters safely

        Args:
            param: The parameter to decode

        Returns:
            Decoded parameter or None
        """
        if not param:
            return None
        
        try:
            param_list = ast.literal_eval(param) 
            return param_list[0].decode('utf-8') if param_list else None # return urllib.parse.unquote(param)
        except Exception:
            return param

    @abstractmethod
    def _get_submit_file_headers(self, filename, metadata):
        """Get headers for file submission

        Args:
            filename: Original filename
            metadata: Additional metadata

        Returns:
            Dictionary of headers
        """
        pass

    @abstractmethod
    def get_sanitized_file_path(self, json_response):
        """Extract sanitized file path from response

        Args:
            json_response: API response

        Returns:
            Path to sanitized file
        """
        pass

    @abstractmethod
    async def retrieve_sanitized_file(self, data_id, apikey, ip=""):
        """Retrieve sanitized file content

        Args:
            data_id: Data ID to retrieve
            apikey: API key for authentication
            ip: IP address of the client

        Returns:
            File content and status code
        """
        pass

    @abstractmethod
    def check_analysis_complete(self, json_response):
        """Check if analysis is complete

        Args:
            json_response: API response

        Returns:
            Boolean indicating completion status
        """
        pass
