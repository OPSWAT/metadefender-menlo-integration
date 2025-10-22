import unittest
import string
from unittest.mock import Mock, patch, MagicMock
import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
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

    def test_init_with_none_config(self):
        """Test initialization with None config"""
        sns = SNSLogHandler(None)
        # When config is None, arn and client are not set
        self.assertFalse(hasattr(sns, 'arn'))
        self.assertFalse(hasattr(sns, 'client'))

    def test_init_with_config(self):
        """Test initialization with valid config"""
        sns = SNSLogHandler(sns_conf)
        self.assertEqual(sns.arn, sns_conf["arn"])
        self.assertIsNotNone(sns.client)

    @patch('metadefender_menlo.log_handlers.SNS_log.boto3')
    def test_init_boto3_client_creation(self, mock_boto3):
        """Test boto3 client creation during initialization"""
        mock_client = Mock()
        mock_boto3.client.return_value = mock_client
        
        sns = SNSLogHandler(sns_conf)
        
        mock_boto3.client.assert_called_once_with('sns', region_name=sns_conf["region"])
        self.assertEqual(sns.client, mock_client)

    def test_get_time(self):
        """Test getTime method"""
        sns = SNSLogHandler(sns_conf)
        time_str = sns.getTime()
        
        # Should return formatted datetime string
        self.assertIsInstance(time_str, str)
        self.assertRegex(time_str, r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}')

    def test_create_message_attributes_scenarios(self):
        """Test createMessageAttributes method scenarios"""
        sns = SNSLogHandler(sns_conf)
        
        test_cases = [
            # (args, expected_keys)
            (None, 0),
            ({}, 0),
            ({"key1": "value1", "key2": "value2"}, 2),
            ({"key1": "value1", "key2": 123}, 1),  # Only string values
            ({"key1": "value1", "key2": None}, 1),  # Only string values
        ]
        
        for args, expected_keys in test_cases:
            with self.subTest(args=args):
                result = sns.createMessageAttributes(args)
                
                if args is None:
                    self.assertEqual(len(result), 0)
                else:
                    self.assertEqual(len(result), expected_keys)
                    
                    # Check structure for string values
                    for key, value in result.items():
                        self.assertIn('DataType', value)
                        self.assertIn('StringValue', value)
                        self.assertEqual(value['DataType'], 'String')

    def test_get_message_data_id_scenarios(self):
        """Test getMessageDataId method scenarios"""
        sns = SNSLogHandler(sns_conf)
        
        test_cases = [
            # (query_args, expected_data_id)
            ({"uuid": [b"test_uuid"]}, "test_uuid"),
            ({"uuid": ["test_uuid"]}, ""),  # Not bytes
            ({}, ""),  # No uuid
            ({"uuid": []}, ""),  # Empty uuid
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
        """Test getCheckMessage method scenarios"""
        sns = SNSLogHandler(sns_conf)
        
        test_cases = [
            # (query_args, expected_sha256)
            ({"sha256": [b"test_sha256"]}, "test_sha256"),
            ({"sha256": ["test_sha256"]}, ""),  # Not bytes
            ({}, ""),  # No sha256
            ({"sha256": []}, ""),  # Empty sha256
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
    def test_emit_success_scenarios(self, mock_filter, mock_set_message, mock_publish):
        """Test emit method success scenarios"""
        sns = SNSLogHandler(sns_conf)
        
        # Test case 1: Filter allows message
        mock_filter.return_value = True
        mock_set_message.return_value = ({"test": "message"}, "test subject")
        
        record = Mock()
        record.args = {"key": "value"}
        record.levelname = "ERROR"
        
        sns.emit(record)
        
        mock_set_message.assert_called_with(record)
        mock_filter.assert_called_with("ERROR", {"test": "message"})
        mock_publish.assert_called_with({"test": "message"}, sns.createMessageAttributes(record.args), "test subject")
        
        # Reset mocks for second test
        mock_set_message.reset_mock()
        mock_filter.reset_mock()
        mock_publish.reset_mock()
        
        # Test case 2: Filter blocks message
        mock_filter.return_value = False
        mock_set_message.return_value = ({"test": "message"}, "test subject")
        
        sns.emit(record)
        
        mock_set_message.assert_called_with(record)
        mock_filter.assert_called_with("ERROR", {"test": "message"})
        mock_publish.assert_not_called()

    def test_emit_recursion_error(self):
        """Test emit method with RecursionError"""
        sns = SNSLogHandler(sns_conf)
        
        with patch.object(sns, 'set_message', side_effect=RecursionError):
            record = Mock()
            
            with self.assertRaises(RecursionError):
                sns.emit(record)

    @patch('builtins.print')
    def test_emit_general_exception(self, mock_print):
        """Test emit method with general exception"""
        sns = SNSLogHandler(sns_conf)
        
        with patch.object(sns, 'set_message', side_effect=Exception("Test error")):
            record = Mock()
            
            sns.emit(record)  # Should not raise
            
            # Check that print was called with the exception object
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            self.assertIsInstance(call_args[0], Exception)

    def test_publish_message_success(self):
        """Test publishMessage method success"""
        sns = SNSLogHandler(sns_conf)
        
        message = {"test": "data"}
        message_attributes = {"key": {"DataType": "String", "StringValue": "value"}}
        subject = "test subject"
        
        with patch.object(sns, 'client') as mock_client:
            sns.publishMessage(message, message_attributes, subject)
            
            mock_client.publish.assert_called_once()
            call_args = mock_client.publish.call_args
            
            self.assertEqual(call_args[1]["TargetArn"], sns_conf["arn"])
            self.assertEqual(call_args[1]["Subject"], "MetaDefender Cloud - test subject")
            self.assertEqual(call_args[1]["MessageAttributes"], message_attributes)
            self.assertEqual(call_args[1]["MessageStructure"], "json")

    def test_publish_message_subject_truncation(self):
        """Test publishMessage method subject truncation"""
        sns = SNSLogHandler(sns_conf)
        
        long_subject = "a" * 100  # Longer than 79 chars
        message = {"test": "data"}
        message_attributes = {}
        
        with patch.object(sns, 'client') as mock_client:
            sns.publishMessage(message, message_attributes, long_subject)
            
            call_args = mock_client.publish.call_args
            expected_subject = "MetaDefender Cloud - " + "a" * 79
            self.assertEqual(call_args[1]["Subject"], expected_subject)

    @patch('builtins.print')
    def test_publish_message_exception(self, mock_print):
        """Test publishMessage method with exception"""
        sns = SNSLogHandler(sns_conf)
        
        with patch.object(sns, 'client') as mock_client:
            mock_client.publish.side_effect = Exception("Publish error")
            
            message = {"test": "data"}
            message_attributes = {}
            subject = "test"
            
            sns.publishMessage(message, message_attributes, subject)
            
            # Check that print was called with the exception object
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0]
            self.assertIsInstance(call_args[0], Exception)


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
