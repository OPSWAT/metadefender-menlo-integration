import unittest
from unittest.mock import MagicMock, patch
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.handlers.inbound_handler import InboundHandler
from fastapi import Request, Response


class TestInboundMetadataHandler(unittest.IsolatedAsyncioTestCase):
    
    @patch('metadefender_menlo.api.handlers.base_handler.MetaDefenderAPI.get_instance')
    def setUp(self, mock_get_instance):
        mock_get_instance.return_value = MagicMock()
        
        self.test_config = {
            'allowlist': {
                'enabled': False
            }
        }
        
        self.handler = InboundHandler(config=self.test_config)
        self.mock_request = MagicMock(spec=Request)
        self.mock_response = MagicMock(spec=Response)

    async def test_handle_post_not_implemented(self):
        result = await self.handler.handle_post(self.mock_request, self.mock_response)
        self.assertEqual(result, {"error": "Not implemented"})
        self.assertEqual(self.mock_response.status_code, 400)

    def test_initialization(self):
        self.assertIsNotNone(self.handler)
        self.assertEqual(self.handler.config, self.test_config)


if __name__ == '__main__':
    unittest.main()
