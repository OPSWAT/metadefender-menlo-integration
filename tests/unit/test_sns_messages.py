import unittest
import string
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler

sns_conf = {
    "region": "us-west-2",
    "arn": "test_arn"
}
StubUserId = "test"
StubSha256 = "test"
StubFileName = "test"
StubData={
    "userId": "test",
    "sha256":"test",
    "ip":"0.0.0.0",
    "filename":"test",
    "url":"test",
    "dataId":"test",
    "uuid":"test"
}

class TestSnsMethods(unittest.TestCase):
    def test_filter_messages(self):
        sns = SNSLogHandler(sns_conf)
        self.assertTrue(sns.filterMessages('ERROR', "test"))
        self.assertFalse(sns.filterMessages('INFO', "test"))
        self.assertFalse(sns.filterMessages('ERROR', ""))

    def test_valid_sns_sanitized_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ("",""))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', '/api/v1/file')
        setattr(request_info, 'query_arguments', {"uuid":[StubData["uuid"].encode("utf8")]})
        setattr(record, "request_info", request_info)

        self.assertTrue(StubData["uuid"] , sns.set_message(record)[0]["DataId"])
        self.assertFalse("Sha256" in sns.set_message(record)[0])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_analysis_result_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ('', ''))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', '/api/v1/result')
        setattr(request_info, 'query_arguments', {"uuid":[StubData["uuid"].encode("utf8")]})
        setattr(record, "request_info", request_info)

        self.assertTrue(StubData["uuid"] , sns.set_message(record)[0]["DataId"])
        self.assertFalse("Sha256" in sns.set_message(record)[0])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_check_existingt_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ('', ''))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', '/api/v1/check')
        setattr(request_info, 'query_arguments', {"sha256":[StubData["sha256"].encode("utf8")]})
        setattr(record, "request_info", request_info)

        self.assertFalse("DataId" in sns.set_message(record)[0])
        self.assertTrue(StubData["sha256"] , sns.set_message(record)[0]["Sha256"])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_submit_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ("",""))

        record = Record()
        request_info = RequestInfo()
        files = Files()
        setattr(files,"filename","test")
        setattr(request_info, 'uri', '/api/v1/submit')
        setattr(request_info, 'query_arguments', '')
        setattr(request_info, "body_arguments", {"sha256":[StubData["sha256"].encode("utf8")],"userid":[StubData["userId"].encode('utf8')]})
        setattr(request_info, 'files', {"files":[{"filename":StubData["filename"]}]})
        setattr(request_info, 'remote_ip', StubData["ip"])
        setattr(record, "request_info", request_info)

        self.assertFalse("DataId" in sns.set_message(record)[0])
        self.assertTrue(StubData["sha256"] , sns.set_message(record)[0]["Sha256"])
        self.assertTrue(StubData["filename"] , sns.set_message(record)[0]["FileName"])
        self.assertTrue(StubData["userId"], sns.set_message(record)[0]["UserId"])
        self.assertTrue(StubData["ip"] in sns.set_message(record)[0]["Ip"])
        self.assertTrue(StubData["url"] , sns.set_message(record)[0]["Url"])


class Body_arguments():
    userid:string
    sha256:string
    srcuri:string

class Record():
    request_info: string
    query_arguments: string
    files: string
    body_arguments: Body_arguments

    def getMessage(self):
        return "hello"

class Files():
    filename:string

class RequestInfo():
    uri: string
    files:Files


if __name__ == '__main__':
    unittest.main()
