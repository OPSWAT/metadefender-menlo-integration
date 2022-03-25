

import sys 
from os import environ
import json
from  logging import Handler
from kafka import KafkaProducer

class KafkaLogHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """

    terminator = '\n'

    def __init__(self, stream=None):
        self.bootstrap_servers='0.0.0.0:9092'
        self.topic='test'
        self.sender =KafkaProducer(bootstrap_servers=self.bootstrap_servers,value_serializer=lambda v: json.dumps(v).encode('utf-8'))
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        Handler.__init__(self)
        if stream is None:
            stream = sys.stderr
        self.stream = stream

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def emit(self, record):
        """
        Emit a record.

        If a formatter is specified, it is used to format the record.
        The record is then written to the stream with a trailing newline.  If
        exception information is present, it is formatted using
        traceback.print_exception and appended to the stream.  If the stream
        has an 'encoding' attribute, it is used to determine how to do the
        output to the stream.
        """
        try:
            msg = {
                    "esIndexName":environ.get("MENLO_ENV"),
                    "type":record.levelname,
                    "id":record.request_id,
                    "region":environ.get("AWS_REGION"),
                    "message":record.getMessage()
                }
            self.sender.send(self.topic, msg)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
