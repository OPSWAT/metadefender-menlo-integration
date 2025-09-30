import logging
import asyncio
import yaml
from fastapi import Request, Response
from metadefender_menlo.api.responses.file_analysis import FileAnalyis
from metadefender_menlo.api.handlers.base_handler import BaseHandler
from metadefender_menlo.api.log_types import SERVICE, TYPE

with open('config.yml', 'r') as file:
    config = yaml.safe_load(file)

if config['timeout']['result']['enabled']:
    timeout = config['timeout']['result']['value']
else:
    timeout = None 

class ResultHandler(BaseHandler):
    """
    Handler for retrieving the result of a file analysis using its UUID.
    """
    timeout = timeout
    print('### timeout: ', timeout)
    def __init__(self):
        super().__init__()

    async def handle_get(self, request: Request, response: Response):
        uuid = request.query_params.get('uuid')
        if not uuid:
            return self.json_response(response, {'error': 'UUID parameter is required'}, 400)
        
        if self.dynamodb:
            item = self.table.get_item(Key={'id': f'ALLOW#{uuid}'}).get('Item')
            if item:
                self.table.delete_item(Key={'id': f'ALLOW#{uuid}'})
                
                return self.json_response(response, {
                    'result': 'completed',
                    'outcome': 'clean',
                    'report_url': '',
                    'filename': item.get('filename', ''),
                    'modifications': ['Domain whitelisted']
                }, 200)

        logging.info("{0} > {1} > {2}".format(
            SERVICE.MenloPlugin, 
            TYPE.Request, 
            {"method": "GET", "endpoint": "/api/v1/result/%s" % uuid}
        ))
        
        await self.prepare_request(request) # TODO: also do the timeout here for request (to MDCL)

        try:
            timeout_value = None
            try:
                if self.timeout is not None:
                    timeout_value = float(self.timeout)
            except Exception:
                timeout_value = None

            if timeout_value is not None:
                json_response, http_status = await asyncio.wait_for(
                    self.meta_defender_api.check_result(uuid, self.apikey, self.client_ip),
                    timeout=timeout_value
                )
            else:
                json_response, http_status = await self.meta_defender_api.check_result(uuid, self.apikey, self.client_ip)

            json_response, http_status = await FileAnalyis(self.apikey).handle_response(json_response, http_status)

            return self.json_response(response, json_response, http_status)
        except asyncio.TimeoutError:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": f"Timeout while retrieving result for {uuid}"}
            ))
            print('### timeouting...')
            return self.json_response(response, {}, 500)
        except Exception as error:
            logging.error("{0} > {1} > {2}".format(
                self.meta_defender_api.service_name, 
                TYPE.Response, 
                {"error": repr(error)}
            ))
            return self.json_response(response, {}, 500)

async def result_handler(request: Request, response: Response):
    return await ResultHandler().handle_get(request, response)
