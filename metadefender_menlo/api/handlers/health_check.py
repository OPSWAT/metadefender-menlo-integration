from metadefender_menlo.api.handlers.base_handler import BaseHandler

class HealthCheckHandler(BaseHandler):
    def __init__(self, new_config=None):
        super().__init__()
        self.config = new_config

    async def handle_request(self, request):
        client_ip = await self.prepare_request(request)
        self.client_ip = client_ip
        
        response = {
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "1.6.8",
            "commitHash": self.config['commitHash'],
            "rule": self.config['scanRule']
        }
        return self.json_response(response)

async def health_check_route(request):
    handler = HealthCheckHandler(request.app['config'])
    return await handler.handle_request(request)
