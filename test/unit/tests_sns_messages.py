import unittest
import string
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler


sns_conf = {
    "region": "us-west-2",
    "arn": "test_arn"
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

        setattr(request_info, 'uri', 'file')
        setattr(request_info, 'query_arguments', '')
        setattr(record, "request_info", request_info)

        self.assertTrue("DataId" in sns.set_message(record)[0])
        self.assertFalse("Sha256" in sns.set_message(record)[0])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_analysis_result_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ('', ''))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', 'result')
        setattr(request_info, 'query_arguments', '')
        setattr(record, "request_info", request_info)

        self.assertTrue("DataId" in sns.set_message(record)[0])
        self.assertFalse("Sha256" in sns.set_message(record)[0])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_check_existingt_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ('', ''))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', 'check')
        setattr(request_info, 'query_arguments', '')
        setattr(record, "request_info", request_info)

        self.assertFalse("DataId" in sns.set_message(record)[0])
        self.assertTrue("Sha256" in sns.set_message(record)[0])
        self.assertFalse("FileName" in sns.set_message(record)[0])
        self.assertFalse("UserId" in sns.set_message(record)[0])

    def test_submit_message(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ("",""))

        record = Record()
        request_info = RequestInfo()

        setattr(request_info, 'uri', 'submit')
        setattr(request_info, 'query_arguments', '')
        setattr(request_info, "body_arguments", "")
        setattr(request_info, 'files', {})
        setattr(record, "request_info", request_info)

        self.assertFalse("DataId" in sns.set_message(record)[0])
        self.assertTrue("Sha256" in sns.set_message(record)[0])
        self.assertTrue("FileName" in sns.set_message(record)[0])
        self.assertTrue("UserId" in sns.set_message(record)[0])


class Record():
    request_info: string
    query_arguments: string
    files: string
    body_arguments: string

    def getMessage(self):
        return "hello"


class RequestInfo():
    uri: string


if __name__ == '__main__':
    unittest.main()
