import tornado
from tornado.web import HTTPError
import logging

from metadefender_menlo.api.responses.file_submit import FileSubmit
from metadefender_menlo.api.handlers.base_handler import BaseHandler
import json
class FileSubmitHandler(BaseHandler):

    async def post(self):
        logging.info(json.dumps({'msg':"POST /api/v1/file > Parse multipart","id":self.id}))   

        #TODO: log errors     
        if len(self.request.files) < 1:
            logging.error(json.dumps({'msg':"No file uploaded > is call originating from Menlo?","id":self.id}))
            raise HTTPError(400, 'No file uploaded')
        elif len(self.request.files) > 1:
            logging.error(json.dumps({'msg':"Too many files uploaded > is call originating from Menlo?","id":self.id}))
            raise HTTPError(400, 'Too many files uploaded')
        
        field_name = list(self.request.files.keys())[0]
        info = self.request.files[field_name][0]
        filename, content_type = info["filename"], info["content_type"]
        fp = info["body"]
        logging.info(json.dumps({'msg':'Submit {0} {1} {2} bytes'.format(filename,content_type,len(fp)),"id":self.id}))

        metadata = {}
        logging.debug("List of headers:")
        for arg in self.request.arguments.keys():
            logging.debug(json.dumps({'msg':"{0}: {1}".format(arg, self.get_argument(arg)),"id":self.id}))
            metadata[arg] = str(self.request.arguments[arg])

        # make request to MetaDefender         
        json_response, http_status = await self.metaDefenderAPI.submit_file(filename,self.id, fp, metadata=metadata)    
        json_response, http_status = FileSubmit().handle_response(http_status, json_response)
        self.json_response(json_response, http_status)