import unittest
import string
from unittest.mock import Mock, patch, MagicMock
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.log_handlers.SNS_log import SNSLogHandler

sns_conf = {
    "region": "us-west-2",
    "arn": "test_arn"
}
StubUserId = "test"
StubSha256 = "test"
StubFileName = "test"
StubData = {
    "userId": "test",
    "sha256": "test",
    "ip": "0.0.0.0",
    "filename": "test",
    "url": "test",
    "dataId": "test",
    "uuid": "test"
}

class TestSnsMethods(unittest.TestCase):

    def test_filter_messages(self):
        sns = SNSLogHandler(sns_conf)
        self.assertTrue(sns.filterMessages('ERROR', "test"))
        self.assertFalse(sns.filterMessages('INFO', "test"))
        self.assertFalse(sns.filterMessages('ERROR', ""))

    def test_set_message_scenarios(self):
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.set_message({}), ("", ""))

        test_cases = [
            ('/api/v1/file', {"uuid": [StubData["uuid"].encode("utf8")]}, "DataId"),
            ('/api/v1/result', {"uuid": [StubData["uuid"].encode("utf8")]}, "DataId"),
            ('/api/v1/check', {"sha256": [StubData["sha256"].encode("utf8")]}, "Sha256"),
            ('/api/v1/submit', {"sha256": [StubData["sha256"].encode("utf8")], "userid": [StubData["userId"].encode('utf8')]}, "FileName")
        ]

        for uri, query_args, expected_field in test_cases:
            record = Record()
            request_info = RequestInfo()
            setattr(request_info, 'uri', uri)
            setattr(request_info, 'query_arguments', query_args)
            setattr(record, "request_info", request_info)

            if uri == '/api/v1/submit':
                files = Files()
                setattr(files, "filename", "test")
                setattr(request_info, 'query_arguments', '')
                setattr(request_info, "body_arguments", query_args)
                setattr(request_info, 'files', {"files": [{"filename": StubData["filename"]}]})
                setattr(request_info, 'remote_ip', StubData["ip"])

            result = sns.set_message(record)
            self.assertNotEqual(result[0], "")
            self.assertNotEqual(result[1], "")

    def test_initialization_scenarios(self):
        test_cases = [
            (None, False, False),
            (sns_conf, True, True)
        ]

        for config, has_arn, has_client in test_cases:
            sns = SNSLogHandler(config)
            if has_arn:
                self.assertEqual(sns.arn, sns_conf["arn"])
                self.assertIsNotNone(sns.client)
            else:
                self.assertFalse(hasattr(sns, 'arn'))
                self.assertFalse(hasattr(sns, 'client'))

    @patch('metadefender_menlo.log_handlers.SNS_log.boto3')
    def test_init_boto3_client_creation(self, mock_boto3):
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client

        sns = SNSLogHandler(sns_conf)

        mock_boto3.client.assert_called_once_with('sns', region_name=sns_conf["region"])
        self.assertEqual(sns.client, mock_client)

    def test_get_time(self):
        sns = SNSLogHandler(sns_conf)
        time_str = sns.getTime()

        self.assertIsInstance(time_str, str)
        self.assertRegex(time_str, r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')

    def test_create_message_attributes_scenarios(self):
        sns = SNSLogHandler(sns_conf)

        test_cases = [
            (None, 0),
            ({}, 0),
            ({"key1": "value1", "key2": "value2"}, 2),
            ({"key1": "value1", "key2": 123}, 1),
            ({"key1": "value1", "key2": None}, 1)
        ]

        for args, expected_keys in test_cases:
            with self.subTest(args=args):
                result = sns.createMessageAttributes(args)

                if args is None:
                    self.assertEqual(len(result), 0)
                else:
                    self.assertEqual(len(result), expected_keys)

                    for key, value in result.items():
                        self.assertIn('DataType', value)
                        self.assertIn('StringValue', value)
                        self.assertEqual(value['DataType'], 'String')

    def test_get_message_data_id_scenarios(self):
        sns = SNSLogHandler(sns_conf)

        test_cases = [
            ({"uuid": [b"test_uuid"]}, "test_uuid"),
            ({"uuid": ["test_uuid"]}, ""),
            ({}, ""),
            ({"uuid": []}, "")
        ]

        for query_args, expected_data_id in test_cases:
            with self.subTest(query_args=query_args):
                record = Mock()
                record.request_info = Mock()
                record.request_info.query_arguments = query_args
                record.getMessage.return_value = "test error"

                result = sns.getMessageDataId(record)

                self.assertEqual(result["DataId"], expected_data_id)
                self.assertEqual(result["ErrorMessage"], "test error")
                self.assertIn("TimeStamp", result)

    def test_get_check_message_scenarios(self):
        sns = SNSLogHandler(sns_conf)

        test_cases = [
            ({"sha256": [b"test_sha256"]}, "test_sha256"),
            ({"sha256": ["test_sha256"]}, ""),
            ({}, ""),
            ({"sha256": []}, "")
        ]

        for query_args, expected_sha256 in test_cases:
            with self.subTest(query_args=query_args):
                record = Mock()
                record.request_info = Mock()
                record.request_info.query_arguments = query_args
                record.getMessage.return_value = "test error"

                result = sns.getCheckMessage(record)

                self.assertEqual(result["Sha256"], expected_sha256)
                self.assertEqual(result["ErrorMessage"], "test error")
                self.assertIn("TimeStamp", result)

    @patch.object(SNSLogHandler, 'publishMessage')
    @patch.object(SNSLogHandler, 'set_message')
    @patch.object(SNSLogHandler, 'filterMessages')
    def test_emit_scenarios(self, mock_filter, mock_set_message, mock_publish):
        sns = SNSLogHandler(sns_conf)

        test_cases = [
            (True, True),
            (False, False)
        ]

        for filter_result, should_publish in test_cases:
            mock_filter.return_value = filter_result
            mock_set_message.return_value = ({"test": "message"}, "test subject")

            record = Mock()
            record.args = {"key": "value"}
            record.levelname = "ERROR"

            sns.emit(record)

            mock_set_message.assert_called_with(record)
            mock_filter.assert_called_with("ERROR", {"test": "message"})
            
            if should_publish:
                mock_publish.assert_called_with({"test": "message"}, sns.createMessageAttributes(record.args), "test subject")
            else:
                mock_publish.assert_not_called()

            mock_set_message.reset_mock()
            mock_filter.reset_mock()
            mock_publish.reset_mock()

    def test_emit_exception_scenarios(self):
        sns = SNSLogHandler(sns_conf)

        with patch.object(sns, 'set_message', side_effect=RecursionError):
            record = Mock()
            with self.assertRaises(RecursionError):
                sns.emit(record)

        with patch.object(sns, 'set_message', side_effect=Exception("Test error")):
            with patch('builtins.print') as mock_print:
                record = Mock()
                sns.emit(record)
                mock_print.assert_called_once()
                call_args = mock_print.call_args[0]
                self.assertIsInstance(call_args[0], Exception)

    def test_publish_message_scenarios(self):
        sns = SNSLogHandler(sns_conf)

        test_cases = [
            ("test subject", "MetaDefender Cloud - test subject"),
            ("a" * 100, "MetaDefender Cloud - " + "a" * 79)
        ]

        for subject, expected_subject in test_cases:
            message = {"test": "data"}
            message_attributes = {"key": {"DataType": "String", "StringValue": "value"}}

            with patch.object(sns, 'client') as mock_client:
                sns.publishMessage(message, message_attributes, subject)

                mock_client.publish.assert_called_once()
                call_args = mock_client.publish.call_args

                self.assertEqual(call_args[1]["TargetArn"], sns_conf["arn"])
                self.assertEqual(call_args[1]["Subject"], expected_subject)
                self.assertEqual(call_args[1]["MessageAttributes"], message_attributes)
                self.assertEqual(call_args[1]["MessageStructure"], "json")

    @patch('builtins.print')
    def test_publish_message_exception(self, mock_print):
        sns = SNSLogHandler(sns_conf)

        with patch.object(sns, 'client') as mock_client:
            mock_client.publish.side_effect = Exception("Publish error")

            message = {"test": "data"}
            message_attributes = {}
            subject = "test"

            sns.publishMessage(message, message_attributes, subject)

            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            self.assertIsInstance(call_args[0], Exception)


class Body_arguments():
    userid: string
    sha256: string
    srcuri: string


class Record():
    request_info: string
    query_arguments: string
    files: string
    body_arguments: Body_arguments

    def getMessage(self):
        return "hello"


class Files():
    filename: string


class RequestInfo():
    uri: string
    files: Files


if __name__ == '__main__':
    unittest.main()