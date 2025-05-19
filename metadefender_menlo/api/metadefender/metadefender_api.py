
from abc import ABC, abstractmethod
import asyncio
import ast
import logging
from httpx import AsyncClient, AsyncByteStream
from metadefender_menlo.api.log_types import SERVICE, TYPE


async def stream_file(file_obj):
    loop = asyncio.get_running_loop()
    while True:
        chunk = await loop.run_in_executor(None, file_obj.read, 8192)
        if not chunk:
            break
        yield chunk

class AsyncFileStream(AsyncByteStream):
    def __init__(self, file_obj):
        super().__init__()
        self.file_obj = file_obj

    async def __aiter__(self):
        async for chunk in stream_file(self.file_obj):
            yield chunk

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
            async with AsyncClient() as client:
                # Use GET with Range header instead of HEAD
                response = await client.get(url, headers=headers)
                return response.headers
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(self.service_name, TYPE.Response, {
                "Exception: ": repr(error)
            }),  {'apikey': self.apikey})
            return {}  # Return empty dict instead of None

    async def submit(self, file_bytes, metadata, apikey='', client_ip=None):
        """Submit a file for scanning

        MDEndpoint:
            /api/v1/submit

        Args:
            filename: Original filename
            file_bytes: Bytes content of the file
            metadata: Additional metadata to send with the file
            apikey: API key for authentication
            ip: IP address of the client

        Returns:
            API response and status code

        """
        headers = self._get_submit_file_headers(metadata, apikey, client_ip)

        url = self.server_url + self.api_endpoints["file_submit"]["endpoint"]

        logging.info("{0} > {1} > {2}".format(self.service_name, TYPE.Request, {
            "message": "Submit file", "url": url, "headers": headers
        }))

        stream = AsyncFileStream(file_bytes)

        async with AsyncClient() as client:
            response = await client.post(
                url,
                content=stream,
                headers=headers
            )

            return response.json(), response.status_code

    async def check_result(self, data_id, apikey, ip=""):
        """Check analysis result for a data_id

        MDEndpoint:
            /api/v1/result/{data_id}

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

        MDEndpoint:
            /api/v1/check?sha256=%s

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

        response['sha256'] = hash_value
        
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

        async with AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, data=data)
            
            # response.json(), response.status_code
            status_code = response.status_code
            content_type = response.headers.get('Content-Type', '')
            
            if 'application/json' in content_type:
                json_response = response.json()
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
        
        async with AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            
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
        
        async with AsyncClient() as client:
            if method == "GET":
                response = await client.get(url, headers=headers)
            elif method == "POST":
                response = await client.post(url, headers=headers, data=data)
            
            status_code = response.status_code
            content = response.read()
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
            return param_list[0].decode('utf-8') if param_list else None
        except Exception:
            return param

    @abstractmethod
    def _get_submit_file_headers(self, metadata, apikey, ip):
        """Get headers for file submission

        Args:
            filename: Original filename
            metadata: Additional metadata,
            apikey: API key for authentication
            ip: IP address of the client

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

        MDEndpoint:
            /api/v1/file?uuid=%s
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
