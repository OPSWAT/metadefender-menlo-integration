

import json
from logging import Handler
import boto3
from datetime import datetime


class SNSLogHandler(Handler):

    def __init__(self, config, stream=None):
        Handler.__init__(self)
        if config != None:
            self.arn = config["arn"]
            self.client = boto3.client('sns', region_name=config["region"])

    def emit(self, record):
        try:
            message = self.set_message(record)
            if self.filterMessages(record.levelname, message):
                self.publishMessage(message)
        except RecursionError:
            raise
        except Exception as e:
            print(e)

            
    def publishMessage(self, message):
        try:
            self.client.publish(
                TargetArn=self.arn,
                Message=json.dumps({"default": json.dumps(message, indent=2)}),
                Subject='MenloMiddleware',
                MessageStructure='json'
            )
        except Exception as error:
            print(error)

    def set_message(self, record):
        if hasattr(record, "request_info"):
            if hasattr(record.request_info, "uri"):
                url = record.request_info.uri
                if "file" in url:
                    # RetrieveSanitized
                    return self.getFileMessage(record)
                if "result" in url:
                    # AnalysisResult
                    return self.getResultMessage(record)
                if "check" in url:
                    # CheckExisting
                    return self.getCheckMessage(record)
                if "submit" in url:
                    # SubmitFile
                    return self.setSubmitMessage(record)
        return ""

    def getFileMessage(self, record):
        return self.getMessageDataId(record)

    def getResultMessage(self, record):
        return self.getMessageDataId(record)

    def getMessageDataId(self, record):
        try:
            data_id = record.request_info.query_arguments["uuid"][0].decode(
            'utf-8')
        except Exception:
            data_id=""
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
            sha256=""
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
            user_id=""
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


