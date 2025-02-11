# coding: utf-8
from datetime import date, datetime  
from typing import List, Dict  

from metadefender_menlo.api.models.base_model import Model
from metadefender_menlo.api import util


class FileAnalysisResponse(Model):

    def __init__(self, result=None, outcome=None, report_url=None, filename=None, modifications=None, sanitized_file_path=None):  
        """FileAnalysisResponse - a model defined in OpenAPI

        :param result: The result of this FileAnalysisResponse.  
        :type result: str
        :param outcome: The outcome of this FileAnalysisResponse.  
        :type outcome: str
        :param report_url: The report_url of this FileAnalysisResponse.  
        :type report_url: str
        :param filename: The filename of this FileAnalysisResponse.  
        :type filename: str
        :param modifications: The modifications of this FileAnalysisResponse.  
        :type modifications: List[str]
        """
        self.types = {
            'result': str,
            'outcome': str,
            'report_url': str,
            'filename': str,
            'modifications': List[str],
            'sanitized_file_path': str
        }

        self.attribute_map = {
            'result': 'result',
            'outcome': 'outcome',
            'report_url': 'report_url',
            'filename': 'filename',
            'modifications': 'modifications',
            'sanitized_file_path': 'sanitized_file_path'
        }

        self._result = result
        self._outcome = outcome
        self._report_url = report_url
        self._filename = filename
        self._modifications = modifications
        self._sanitized_file_path = sanitized_file_path

    @classmethod
    def from_dict(cls, dikt) -> 'FileAnalysisResponse':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The FileAnalysisResponse of this FileAnalysisResponse.  
        :rtype: FileAnalysisResponse
        """
        return util.deserialize_model(dikt, cls)

    @property
    def result(self):
        """Gets the result of this FileAnalysisResponse.

        The current status of the analysis  

        :return: The result of this FileAnalysisResponse.
        :rtype: str
        """
        return self._result

    @result.setter
    def result(self, result):
        """Sets the result of this FileAnalysisResponse.

        The current status of the analysis  

        :param result: The result of this FileAnalysisResponse.
        :type result: str
        """
        allowed_values = ["pending", "completed"]  
        if result not in allowed_values:
            raise ValueError(
                "Invalid value for `result` ({0}), must be one of {1}"
                .format(result, allowed_values)
            )

        self._result = result

    @property
    def outcome(self):
        """Gets the outcome of this FileAnalysisResponse.

        The overall analysis result.  

        :return: The outcome of this FileAnalysisResponse.
        :rtype: str
        """
        return self._outcome

    @outcome.setter
    def outcome(self, outcome):
        """Sets the outcome of this FileAnalysisResponse.

        The overall analysis result.  

        :param outcome: The outcome of this FileAnalysisResponse.
        :type outcome: str
        """
        allowed_values = ["clean", "infected", "unknown", "error"]  
        if outcome not in allowed_values:
            raise ValueError(
                "Invalid value for `outcome` ({0}), must be one of {1}"
                .format(outcome, allowed_values)
            )

        self._outcome = outcome

    @property
    def report_url(self):
        """Gets the report_url of this FileAnalysisResponse.

        A full URL to retrieve the report  

        :return: The report_url of this FileAnalysisResponse.
        :rtype: str
        """
        return self._report_url

    @report_url.setter
    def report_url(self, report_url):
        """Sets the report_url of this FileAnalysisResponse.

        A full URL to retrieve the report  

        :param report_url: The report_url of this FileAnalysisResponse.
        :type report_url: str
        """
        if report_url is None:
            raise ValueError("Invalid value for `report_url`, must not be `None`")  

        self._report_url = report_url

    @property
    def filename(self):
        """Gets the filename of this FileAnalysisResponse.

        Optional string of new filename. If not given, will use original  

        :return: The filename of this FileAnalysisResponse.
        :rtype: str
        """
        return self._filename

    @filename.setter
    def filename(self, filename):
        """Sets the filename of this FileAnalysisResponse.

        Optional string of new filename. If not given, will use original  

        :param filename: The filename of this FileAnalysisResponse.
        :type filename: str
        """

        self._filename = filename

    @property
    def modifications(self):
        """Gets the modifications of this FileAnalysisResponse.

        Array of up to 5 strings of modifications performed on the file by CDR.    

        :return: The modifications of this FileAnalysisResponse.
        :rtype: List[str]
        """
        return self._modifications

    @modifications.setter
    def modifications(self, modifications):
        """Sets the modifications of this FileAnalysisResponse.

        Array of up to 5 strings of modifications performed on the file by CDR.    

        :param modifications: The modifications of this FileAnalysisResponse.
        :type modifications: List[str]
        """

        self._modifications = modifications

    @property
    def sanitized_file_path(self):
        """Gets the sanitized_file_path of this FileAnalysisResponse.

        A full URL to retrieve the sanitized file  

        :return: The sanitized_file_path of this FileAnalysisResponse.
        :rtype: str
        """
        return self._sanitized_file_path

    @sanitized_file_path.setter
    def sanitized_file_path(self, sanitized_file_path):
        """Sets the sanitized_file_path of this FileAnalysisResponse.

        A full URL to retrieve the report  

        :param sanitized_file_path: The sanitized_file_path of this FileAnalysisResponse.
        :type sanitized_file_path: str
        """
        if sanitized_file_path is None:
            raise ValueError("Invalid value for `sanitized_file_path`, must not be `None`")  

        self._sanitized_file_path = sanitized_file_path
