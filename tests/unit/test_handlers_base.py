import unittest
from unittest.mock import MagicMock, patch
import json
from tornado.httputil import HTTPServerRequest

import sys
import os
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.metadefender.metadefender_api import MetaDefenderAPI
from metadefender_menlo.api.handlers.base_handler import BaseHandler, LogRequestFilter, request_id_var, request_context

class TestBaseHandler(unittest.TestCase):

    def setUp(self):
        self.request_mock = MagicMock(spec=HTTPServerRequest)
        self.request_mock.headers = {}
        self.request_mock.remote_ip = '127.0.0.1'
        self.request_mock.connection = MagicMock()  
        self.handler = BaseHandler(MagicMock(), self.request_mock)

    def test_prepare_with_request_id(self):
        self.request_mock.headers = {'request-id': 'test-id'}
        self.handler.prepare()
        self.assertEqual(request_id_var.get(), 'test-id')
        self.assertEqual(request_context.get(), self.request_mock)

    def test_prepare_without_request_id(self):
        self.handler.prepare()
        self.assertIsNotNone(request_id_var.get())
        self.assertNotEqual(request_id_var.get(), '')
        self.assertEqual(request_context.get(), self.request_mock)

    @patch.object(MetaDefenderAPI, 'get_instance')
    def test_initialize(self, mock_get_instance):
        mock_api = MagicMock()
        mock_get_instance.return_value = mock_api
        
        # Reserved IP address used for testing/documentation purposes
        self.request_mock.headers = {'X-Real-IP': '192.0.2.1'}
        self.handler.initialize()
        self.assertEqual(self.handler.meta_defender_api, mock_api)
        self.assertEqual(self.handler.client_ip, '192.0.2.1')

        self.request_mock.headers = {'X-Forwarded-For': '198.51.100.1'}
        self.handler.initialize()
        self.assertEqual(self.handler.client_ip, '198.51.100.1')

        self.request_mock.headers = {}
        self.handler.initialize()
        self.assertEqual(self.handler.client_ip, '127.0.0.1')


    @patch('logging.info')
    def test_json_response(self, mock_logging):
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.write = MagicMock()

        data = {'key': 'value'}
        self.handler.json_response(data, 201)

        mock_logging.assert_called_once()
        self.handler.set_status.assert_called_once_with(201)
        self.handler.set_header.assert_called_once_with("Content-Type", 'application/json')
        self.handler.write.assert_called_once_with(json.dumps(data))

    @patch('logging.info')
    def test_json_response_204(self, mock_logging):
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.write = MagicMock()

        data = None
        self.handler.json_response(data, 204)

        mock_logging.assert_called_once()
        self.handler.set_status.assert_called_once_with(204)
        self.handler.set_header.assert_called_once_with("Content-Type", 'application/json')
        self.handler.write.assert_not_called()

    def test_stream_response(self):
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.write = MagicMock()

        data = b'binary data'
        self.handler.stream_response(data, 200)

        self.handler.set_status.assert_called_once_with(200)
        self.handler.set_header.assert_called_once_with("Content-Type", 'application/octet-stream')
        self.handler.write.assert_called_once_with(data)

    def test_stream_response_204(self):
        self.handler.set_status = MagicMock()
        self.handler.set_header = MagicMock()
        self.handler.write = MagicMock()

        data = None
        self.handler.stream_response(data, 204)

        self.handler.set_status.assert_called_once_with(204)
        self.handler.set_header.assert_called_once_with("Content-Type", 'application/octet-stream')
        self.handler.write.assert_not_called()

class TestLogRequestFilter(unittest.TestCase):

    def setUp(self):
        self.filter = LogRequestFilter()

    def test_filter(self):
        record = MagicMock()
        request_id_var.set('test-id')
        request_context.set('test-context')

        result = self.filter.filter(record)

        self.assertTrue(result)
        self.assertEqual(record.request_id, 'test-id')
        self.assertEqual(record.request_info, 'test-context')

if __name__ == '__main__':
    unittest.main()