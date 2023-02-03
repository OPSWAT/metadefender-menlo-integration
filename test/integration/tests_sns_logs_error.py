from unittest.mock import AsyncMock
from tornado.testing import AsyncHTTPTestCase
from metadefender_menlo import __main__

class TestHelloApp(AsyncHTTPTestCase):
    sns_log = None
    headers = {'Authorization': "testApiKey"}

    def logMethod(self, message):
        self.sns_log = message

    def get_app(self):
        __main__.MetaDefenderAPI._request_as_json_status = AsyncMock(
            return_value="")

        __main__.initial_config(
            './config.yml', './metadefender_menlo/conf/sns-config.json')

        __main__.SNSLogHandler.publishMessage = self.logMethod
        return __main__.make_app()

    def test_endpoint__retrieve_sanitized__sns_logs_error(self):
        self.fetch('/api/v1/file?uuid=test',
                   method="GET", headers=self.headers)
        self.assertNotEqual(self.sns_log, None)
        self.sns_log = None

    def test_endpoint__get_result__sns_logs_error(self):
        self.fetch('/api/v1/result?uuid=test',
                   method="GET", headers=self.headers)
        self.assertNotEqual(self.sns_log, None)
        self.sns_log = None

    def test_endpoint__check_existing__sns_logs_error(self):
        self.fetch('/api/v1/check?sha256=test',
                   method="GET", headers=self.headers)
        self.assertNotEqual(self.sns_log, None)
        self.sns_log = None

    def test_endpoint__submit_file__sns_logs_error(self):
        self.fetch('/api/v1/submit', method="POST",
                   body="", headers=self.headers)
        self.assertNotEqual(self.sns_log, None)
        self.sns_log = None
