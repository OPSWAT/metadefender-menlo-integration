

from  logging import Handler
import os
import sys 
from kafka_messaging import Sender
import json
from datetime import datetime
import time
from os import environ
import json
class KafkaLogHandler(Handler):
    """
    A handler class which writes logging records, appropriately formatted,
    to a stream. Note that this class does not close the stream, as
    sys.stdout or sys.stderr may be used.
    """

    terminator = '\n'

    def __init__(self, stream=None):
        self.sender = Sender(ip="0.0.0.0", port=9092, acks=0)
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
            now = datetime.now()
            info={
                "msg":record.getMessage(),
                "id":""
                }
            try:
                info_=record.getMessage()
                info=json.loads(info_)
            except Exception as e:
                e="id not found"
            msg = {
                    "esIndexName":environ.get("ENV"),
                    "timestamp":now.strftime("%H:%M:%S"),
                    "type":record.levelname,
                    "id":info["id"],
                    "region":environ.get("AWS_REGION"),
                    "message":info["msg"]
                }
            self.sender.send("test", msg=json.dumps(msg))
            print(msg)
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
