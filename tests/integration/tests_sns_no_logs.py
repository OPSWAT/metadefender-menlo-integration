
from tornado.testing import AsyncHTTPTestCase
from unittest.mock import AsyncMock, Mock
from metadefender_menlo import __main__

class TestHelloApp(AsyncHTTPTestCase):
    sns_log = None
    headers = {'Authorization': "testApiKey"}

    def logMethod(self, message):
        self.sns_log = message

    def get_app(self):
        __main__.MetaDefenderAPI._request_as_json_status = AsyncMock(
            return_value=({}, 200))
        
        file = {'file': [{'filename': 'file.txt',
                           'body': b'hello world', 'content_type': 'text/plain'}]}
        __main__.FileSubmitHandler.validateFile = Mock(
            return_value=(file)
        )
        __main__.initial_config(
            './config.yml', './metadefender_menlo/conf/sns-config.json')
        __main__.SNSLogHandler.publishMessage = self.logMethod

        return __main__.make_app()

    def test_endpoint__retrieve_sanitized__no_sns_logs(self):
        self.fetch('/api/v1/file?uuid=test',
                   method="GET", headers=self.headers)
        self.assertEqual(self.sns_log, None)

    def test_endpoint__get_result__no_sns_logs(self):
        self.fetch('/api/v1/result?uuid=test',
                   method="GET", headers=self.headers)
        self.assertEqual(self.sns_log, None)

    def test_endpoint__check_existing__no_sns_logs(self):
        self.fetch('/api/v1/check?sha256=test',
                   method="GET", headers=self.headers)
        self.assertEqual(self.sns_log, None)

    def test_endpoint__submit_file__no_sns_logs(self):
        self.fetch('/api/v1/submit', method="POST",
                   body="", headers=self.headers)
        self.assertEqual(self.sns_log, None)
