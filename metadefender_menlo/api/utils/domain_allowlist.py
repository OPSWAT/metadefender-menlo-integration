import boto3
from urllib.parse import urlparse

class DomainAllowlistUtils:
        """
        Allowlist Handler class that provides common functionality for all handlers.
        """

        def __init__(self, config):
            self.config = config
            self.domains_cache = {}
            self.enabled = False
            self._init_aws_resources()

        def _init_aws_resources(self):
            if self.config['allowlist'].get('enabled'):
                try:
                    session = boto3.Session(profile_name=self.config['allowlist'].get('aws_profile', 'default'))
                    self.dynamodb = session.resource('dynamodb')
                    self.table = self.dynamodb.Table(self.config['allowlist']['db_table_name'])
                    self.enabled = True
                except Exception:
                    self.dynamodb = None
                    self.table = None
        
        def extract_domain(self, u: str ) -> str:
            hostname = urlparse(u).hostname or u
            parts = hostname.split('.')
            return ".".join(parts[-2:])

        def add_to_allowlist(self, http_status: int, uuid: str, srcuri: str, filename: str, apikey: str):
            if http_status == 200 and uuid:

                    domains = self.get_cached_domains(apikey)
                    if domains:
                        domain = self.extract_domain(srcuri)
                        normalized_domains = {self.extract_domain(d) for d in domains}

                        if domain in normalized_domains:
                            metadata_item = {
                                'id': f'ALLOW#{uuid}',
                                'filename': filename
                            }
                            self.table.put_item(Item=metadata_item)
        
        def is_allowlist_enabled(self, uuid: str):
            return self.enabled and self.dynamodb

        def get_cached_domains(self, api_key: str) -> list:
            """Get cached domains for an API key"""
            if not self.enabled:
                return []
                
            if api_key not in self.domains_cache:
                api_key_response = self.table.get_item(Key={'id': f'APIKEY#{api_key}'})
                self.domains_cache[api_key] = api_key_response.get('Item', {}).get('domains', [])
            return self.domains_cache.get(api_key, [])

        def is_in_allowlist(self, uuid: str):
            item = self.table.get_item(Key={'id': f'ALLOW#{uuid}'}).get('Item')
            if item:
                self.table.delete_item(Key={'id': f'ALLOW#{uuid}'})
                
                return {
                    'result': 'completed',
                    'outcome': 'clean',
                    'report_url': '',
                    'filename': item.get('filename', ''),
                    'modifications': ['Domain whitelisted']
                }, 200
            return None, None

