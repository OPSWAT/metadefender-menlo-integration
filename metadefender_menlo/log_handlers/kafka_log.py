

import json
from  logging import Handler
from kafka import KafkaProducer

class KafkaLogHandler(Handler):

    terminator = '\n'
    settings = None

    def __init__(self, config, kafka_config, stream=None):
        Handler.__init__(self)
        self.settings = config
        environment_name="menlo_middleware_" + self.settings['env']
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
        if not hasattr(record, "request_id"):
            record.request_id = 'internal'
        
        try:
            msg = {
                    "esIndexName": self.settings['env'],
                    "type":record.levelname,
                    "id":record.request_id,
                    "region": self.settings['region'],
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
