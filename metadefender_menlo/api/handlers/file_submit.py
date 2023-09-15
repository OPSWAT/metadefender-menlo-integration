
import logging
from tornado.web import HTTPError
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.responses.file_submit import FileSubmit

class FileSubmitHandler(BaseHandler):
    
    async def post(self):
        
        files = self.validateFile()
        field_name = list(files.keys())[0]
        info = files[field_name][0]
        filename, content_type, fp = info["filename"], info["content_type"], info["body"]
        
        apikey = self.request.headers.get('Authorization')

        logging.info("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
            "method": "POST", "fileName": filename, "endpoint": "/api/v1/file",
            "content_type": content_type, "dimension": "{0} bytes".format(len(fp))
        }))

        metadata = {}
        logging.debug("List of headers:")
        for arg in self.request.arguments.keys():
            logging.debug("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
                "headers": "{0} : {1}".format(arg, self.get_argument(arg))
            }))
            metadata[arg] = str(self.request.arguments[arg])

        try:
            json_response, http_status = await self.metaDefenderAPI.submit_file(filename, fp, metadata=metadata, apikey=apikey, ip=self.client_ip)
            json_response, http_status = FileSubmit().handle_response(http_status, json_response)
            self.json_response(json_response, http_status)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                SERVICE.MenloPlugin, TYPE.Internal, {"error": repr(error)}))
            self.json_response({}, 500)

    def validateFile(self):
        if len(self.request.files) < 1:
            logging.error("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
                "message": "No file uploaded > is call originating from Menlo?"
            }))
            raise HTTPError(400, 'No file uploaded')
        if len(self.request.files) > 1:
            logging.error("{0} > {1} > {2}".format(SERVICE.MenloPlugin, TYPE.Request, {
                "message": "Too many files uploaded > is call originating from Menlo?"
            }))
            raise HTTPError(400, 'Too many files uploaded')
        return self.request.files
