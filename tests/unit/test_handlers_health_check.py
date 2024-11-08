import unittest
from unittest.mock import Mock, patch
import json
import logging

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.log_types import SERVICE, TYPE
from metadefender_menlo.api.handlers.health_check import HealthCheckHandler

class TestHealthCheckHandler(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.application = Mock()
        self.application.ui_methods = {}
        self.application.ui_modules = {}

        self.request = Mock()
        self.request.connection = Mock()
        self.request.connection.context = {}

        self.test_config = {
            'commitHash': 'abc123',
            'scanRule': 'test-rule'
        }

        self.handler = HealthCheckHandler(
            application=self.application,
            request=self.request,
            newConfig=self.test_config,
        )

        self.original_logging_debug = logging.debug
        logging.debug = Mock()
        

    def tearDown(self):
        """Clean up after each test method."""
        logging.debug = self.original_logging_debug

    def test_initialize(self):
        """Test the initialize method with new config."""
        with patch.object(self.handler, 'initialize') as mock_super_init:
            self.handler.initialize(self.test_config)
            
            self.assertEqual(self.handler.settings, self.test_config)
            mock_super_init.assert_called_once_with(self.test_config)

    def test_get(self):
        """Test the GET method response."""
        self.handler.settings = self.test_config
        self.handler.set_status = Mock()
        self.handler.set_header = Mock()
        self.handler.write = Mock()

        expected_response = {
            "status": "Ready",
            "name": "MetaDefender - Menlo integration",
            "version": "1.6.1",
            "commitHash": self.test_config['commitHash'],
            "rule": self.test_config['scanRule']
        }

        self.handler.get()

        logging.debug.assert_called_once_with(
            "{0} > {1} > {2}".format(
                SERVICE.MenloPlugin,
                TYPE.Internal,
                {"message": "GET /health > OK!"}
            )
        )

        self.handler.set_status.assert_called_once_with(200)
        self.handler.set_header.assert_called_once_with(
            "Content-Type",
            'application/json'
        )

        self.handler.write.assert_called_once_with(
            json.dumps(expected_response)
        )

    def test_get_response_format(self):
        """Test the exact format and content of the GET response."""
        self.handler.settings = self.test_config
        self.handler.set_status = Mock()
        self.handler.set_header = Mock()
        self.handler.write = Mock()

        self.handler.get()

        written_data = self.handler.write.call_args[0][0]
        response_dict = json.loads(written_data)

        self.assertIn('status', response_dict)
        self.assertIn('name', response_dict)
        self.assertIn('version', response_dict)
        self.assertIn('commitHash', response_dict)
        self.assertIn('rule', response_dict)

        self.assertEqual(response_dict['status'], 'Ready')
        self.assertEqual(response_dict['name'], 'MetaDefender - Menlo integration')
        self.assertEqual(response_dict['version'], '1.6.1')
        self.assertEqual(response_dict['commitHash'], self.test_config['commitHash'])
        self.assertEqual(response_dict['rule'], self.test_config['scanRule'])


if __name__ == '__main__':
    unittest.main()
