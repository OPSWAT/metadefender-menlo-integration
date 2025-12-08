from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler

class InboundHandler(BaseHandler):
    """
    Handler for processing inbound metadata.
    """
    def __init__(self, config=None):
        super().__init__(config)

    async def handle_post(self, request, response):
        response.status_code = 400
        return {"error": "Not implemented"}

        
async def inbound_handler(request: Request, response: Response):
    return await InboundHandler(request.app.state.config).handle_post(request, response)