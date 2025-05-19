from fastapi import Request, Response
from metadefender_menlo.api.handlers.base_handler import BaseHandler

class HealthHandler(BaseHandler):
    """
    Handler for checking the health of the Menlo integration.
    """
    def __init__(self, config=None):
        super().__init__()
        self.config = config

    async def handle_request(self, request: Request, response: Response):
        return {
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "2.0.0",
            "commitHash": self.config['commitHash'],
            "rule": self.config['scanRule']
        }
        

async def health_handler(request: Request, response: Response):
    return await HealthHandler(request.app.state.config).handle_request(request, response)
