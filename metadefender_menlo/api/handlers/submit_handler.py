import asyncio
import os
import logging
from urllib.parse import urlparse
from fastapi import Request, Response
from httpx import AsyncByteStream
from starlette.datastructures import FormData, UploadFile
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.responses.submit_response import SubmitResponse


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

class SubmitHandler(BaseHandler):
    """
    Handler for submitting files to MetaDefender.
    """
    def __init__(self):
        super().__init__()


    def extract_domain(self, u: str ) -> str:
        hostname = urlparse(u).hostname or u
        parts = hostname.split('.')
        return ".".join(parts[-2:])

    def add_to_allowlist(self, http_status: int, uuid: str, srcuri: str, filename: str):
        if http_status == 200 and uuid:
                
                domains = self.get_cached_domains(self.apikey)
                if domains:
                    domain = self.extract_domain(srcuri)
                    normalized_domains = {self.extract_domain(d) for d in domains}

                    if domain in normalized_domains:
                        metadata_item = {
                            'id': f'ALLOW#{uuid}',
                            'filename': filename
                        }
                        self.table.put_item(Item=metadata_item)

    async def handle_post(self, request: Request, response: Response):
        if not request.headers.get("content-type").startswith('multipart/'):
            return self.json_response(response, {"error": "Content-Type must be multipart/form-data"}, 400)
        
        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "POST", "endpoint": "/api/v1/submit"}
        ))

        await self.prepare_request(request)

        try:
            form: FormData = await request.form()
            upload: UploadFile = form.get("files") or form.get("file")
            if upload.size == 0:
                raise ValueError("Empty file detected")
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Internal, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {"error": "No file uploaded"}, 400)

        if not isinstance(upload, UploadFile):
            return self.json_response(response, {"error": "No file uploaded"}, 400)
                
        content_length = None
        if self.meta_defender_api.service_name == SERVICE.MetaDefenderCore:
            upload.file.seek(0, os.SEEK_END)
            content_length = upload.file.tell()
            upload.file.seek(0)

        if content_length == 0:
            return self.json_response(response, {"error": "Empty file detected"}, 400)

        # form data
        metadata = {}
        metadata['userid'] = form.get("userid")
        metadata['srcuri'] = form.get("srcuri")
        metadata['filename'] = form.get("filename") or upload.filename
        metadata['content-length'] = content_length
        metadata = {k: v for k, v in metadata.items() if v is not None}
        
        try:
            json_response, http_status = await self.meta_defender_api.submit(upload.file, metadata, self.apikey, self.client_ip)
            json_response, http_status = await SubmitResponse().handle_response(json_response, http_status)

            uuid = json_response.get('uuid')
            if self.dynamodb:
                self.add_to_allowlist(http_status, uuid, metadata.get('srcuri', ''), metadata.get('filename', ''))
            
            return self.json_response(response, json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Internal, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def submit_handler(request: Request, response: Response):
    return await SubmitHandler().handle_post(request, response)