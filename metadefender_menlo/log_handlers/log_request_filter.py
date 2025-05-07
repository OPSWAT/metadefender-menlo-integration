import logging
import contextvars

request_id_context = contextvars.ContextVar("request_id")
request_context = contextvars.ContextVar("request")

class LogRequestFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_context.get('-')
        record.request_info = request_context.get("")
        return True