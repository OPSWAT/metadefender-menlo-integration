

import json
from logging import Handler
import boto3
from datetime import datetime


class SNSLogHandler(Handler):

    def __init__(self, config):
        Handler.__init__(self)
        if config != None:
            self.arn = config["arn"]
            self.client = boto3.client('sns', region_name=config["region"])

    def emit(self, record):
        try:
            message, subject = self.set_message(record)
            if self.filterMessages(record.levelname, message):
                # Note: record.args should contain only string values in its properties
                message_attributes = self.createMessageAttributes(record.args)
                self.publishMessage(message, message_attributes, subject)
        except RecursionError:
            raise
        except Exception as e:
            print(e)

    def publishMessage(self, message, message_attributes, subject):
        try:
            # Subject property can have a max of 100 characters (21 already used by 'MetaDefender Cloud - ')
            subject = subject[:79]
            self.client.publish(
                TargetArn=self.arn,
                Message=json.dumps({"default": json.dumps(message, indent=2)}),
                Subject="MetaDefender Cloud - "+subject,
                MessageAttributes=message_attributes,
                MessageStructure='json'
            )
        except Exception as error:
            print(error)

    def set_message(self, record):
        subject_retrieve = "Retrieve analysis result failed for: "
        if hasattr(record, "request_info"):
            if hasattr(record.request_info, "uri"):
                url = record.request_info.uri
                if "/api/v1/file" in url:
                    # RetrieveSanitized
                    message = self.getFileMessage(record)
                    return message, subject_retrieve+"{0}".format(message["DataId"])
                if "/api/v1/result" in url:
                    # AnalysisResult
                    message = self.getResultMessage(record)
                    return message, subject_retrieve+"{0}".format(message["DataId"])
                if "/api/v1/check" in url:
                    # CheckExisting
                    message = self.getCheckMessage(record)
                    return message, subject_retrieve+"{0}".format(message["Sha256"])
                if "/api/v1/submit" in url:
                    # SubmitFile
                    message = self.setSubmitMessage(record)
                    return message, "Processing failed for file: {0}".format(message["FileName"])
        return "", ""

    def getFileMessage(self, record):
        return self.getMessageDataId(record)

    def getResultMessage(self, record):
        return self.getMessageDataId(record)

    def getMessageDataId(self, record):
        try:
            data_id = record.request_info.query_arguments["uuid"][0].decode(
                'utf-8')
        except Exception:
            data_id = ""
        return {
            "TimeStamp": self.getTime(),
            "DataId": data_id,
            "ErrorMessage": record.getMessage()
        }

    def getCheckMessage(self, record):
        try:
            sha256 = record.request_info.query_arguments["sha256"][0].decode(
                'utf-8')
        except Exception:
            sha256 = ""
        return {
            "TimeStamp": self.getTime(),
            "Sha256": sha256,
            "ErrorMessage": record.getMessage()
        }

    def setSubmitMessage(self, record):
        if len(record.request_info.files.keys()) == 1:
            field_name = list(record.request_info.files.keys())[0]
            file_name = record.request_info.files[field_name][0]["filename"]
        else:
            file_name = ""
        try:
            user_id = record.request_info.body_arguments['userid'][0].decode(
                "utf-8")
        except Exception:
            user_id = ""
        try:
            sha256 = record.request_info.body_arguments['sha256'][0].decode(
                "utf-8")
        except Exception:
            sha256=""
        try:
            srcuri = record.request_info.body_arguments['srcuri'][0].decode(
                "utf-8")
        except Exception:
            srcuri=""
        try:
            remote_ip = record.request_info.remote_ip
        except Exception:
            remote_ip=""
        return {
            "TimeStamp": self.getTime(),
            "FileName": file_name,
            "UserId": user_id,
            "Sha256": sha256,
            "Url":srcuri,
            "Ip":remote_ip,
            "Error message": record.getMessage()
        }

    def filterMessages(self, levelname, message):
        return levelname == "ERROR" and message != ""

    def getTime(self):
        return datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    def createMessageAttributes(self, args):
        message_attributes = {}

        if args is not None and isinstance(args, dict):
            for key, value in args.items():
                if isinstance(value, str):
                    message_attributes[key] = {
                        'DataType': 'String',
                        'StringValue': value
                    }

        return message_attributes