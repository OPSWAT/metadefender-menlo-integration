import tornado
from tornado.web import HTTPError
import logging

from metadefender_menlo.api.responses.file_submit import FileSubmit
from metadefender_menlo.api.handlers.base_handler import BaseHandler
class FileSubmitHandler(BaseHandler):

    async def post(self):
        logging.info("POST /api/v1/file > Parse multipart")   
        apikey = self.request.headers.get('Authorization')
        #TODO: log errors     
        if len(self.request.files) < 1:
            logging.error("No file uploaded > is call originating from Menlo?")
            raise HTTPError(400, 'No file uploaded')
        elif len(self.request.files) > 1:
            logging.error("Too many files uploaded > is call originating from Menlo?")
            raise HTTPError(400, 'Too many files uploaded')
        
        field_name = list(self.request.files.keys())[0]
        info = self.request.files[field_name][0]
        filename, content_type = info["filename"], info["content_type"]
        fp = info["body"]
        logging.info('Submit {0} {1} {2} bytes'.format(filename,content_type,len(fp)))

        metadata = {}
        logging.debug("List of headers:")
        for arg in self.request.arguments.keys():
            logging.debug("{0}: {1}".format(arg, self.get_argument(arg)))
            metadata[arg] = str(self.request.arguments[arg])

        # make request to MetaDefender         
        json_response, http_status = await self.metaDefenderAPI.submit_file(filename, fp, metadata=metadata, apikey=apikey)    
        json_response, http_status = FileSubmit().handle_response(http_status, json_response)
        self.json_response(json_response, http_status)
