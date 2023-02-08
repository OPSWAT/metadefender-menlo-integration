

from queue import Empty
import sys 
from os import environ
import json
from  logging import Handler
from kafka import KafkaProducer
class KafkaLogHandler(Handler):

    terminator = '\n'

    def __init__(self,kafka_config, stream=None):        
        Handler.__init__(self)
        environment_name="menlo_middleware_"+environ.get("MENLO_ENV",'local')
        connection=kafka_config[environment_name]
        self.bootstrap_servers=connection["SERVER"]
        self.topic=connection["TOPIC"]
        self.security_protocol=connection["SSL"]
        
        try:
            if self.security_protocol:
                self.sender = KafkaProducer(security_protocol="SSL",retries=0,bootstrap_servers=self.bootstrap_servers,value_serializer=lambda v: json.dumps(v).encode('utf-8'))
            else:
                self.sender = KafkaProducer(bootstrap_servers=self.bootstrap_servers,retries=0,value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        except Exception:
            pass

    def emit(self, record):
        if not record.request_id:
            record.request_id = 'internal'
        
        try:
            msg = {
                    "esIndexName":environ.get("MENLO_ENV", "dev"),
                    "type":record.levelname,
                    "id":record.request_id,
                    "region":environ.get("AWS_REGION", "us-west-2"),
                    "message":record.getMessage()
                }
            try:
                self.sender.send(self.topic, msg)
            except Exception:
                pass
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
