from tornado.web import RequestHandler
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
import json
import logging
import uuid
import json 

class BaseHandler(RequestHandler):

    def initialize(self):
        self.metaDefenderAPI = MetaDefenderAPI.get_instance()

    # def prepare(self):
    #     authorization_token = self.request.headers.get('Authorization')
        
    #     if authorization_token:
    #         self.metaDefenderAPI.apikey = authorization_token
        self.id=str(uuid.uuid4())
    def json_response(self, data, status_code=200):
        logging.info(json.dumps({'msg':"{0} response: {1}".format(status_code, data),'id':self.id}))
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/json')
        self.write(json.dumps(data))

    def stream_response(self, data, status_code=200):  
        logging.info(json.dumps({'msg':"{0} response: {1}".format(status_code, "sanitized file (binary data)"),"id":self.id}))      
        self.set_status(status_code)
        self.set_header("Content-Type", 'application/octet-stream')
        self.write(data)