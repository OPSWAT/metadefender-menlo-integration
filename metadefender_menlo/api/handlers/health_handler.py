from fastapi import Request, Response
import logging
from metadefender_menlo.api.handlers.base_handler import BaseHandler

class HealthHandler(BaseHandler):
    """
    Handler for checking the health of the Menlo integration.
    """
    def __init__(self, config=None):
        super().__init__(config)
        self.config = config
        cfg = self.config or {}
        self.base_response = {
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "2.0.2",
            "commitHash": cfg.get('commitHash', '-'),
            "rule": cfg.get('scanRule')
        }

    async def handle_request(self, request: Request, response: Response):

        self.prepare_request(request)
        api_type = (self.config or {}).get('api', {}).get('type')
        if api_type == 'core':
            
            json_response, http_status = await self.meta_defender_api.check_core_health(
                self.config['api']['params']['apikey']
            )

            if http_status != 200:
                logging.error(f"Error checking MetaDefender Core health: {http_status, json_response}")
                return self.base_response | {'md_'+api_type: {"status": "Error checking MetaDefender Core Health", "code": http_status}}
                
            return self.base_response | {'md_'+api_type: self.json_response(response, json_response, http_status)}
        else:
            return self.base_response
        

async def health_handler(request: Request, response: Response):
    return await HealthHandler(request.app.state.config).handle_request(request, response)
