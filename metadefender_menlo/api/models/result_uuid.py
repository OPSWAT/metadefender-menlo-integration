# coding: utf-8
from datetime import date, datetime  
from typing import List, Dict  

from metadefender_menlo.api.models.base_model import Model
from metadefender_menlo.api.models.base_model import util

class ResultUUID(Model):

    def __init__(self, result=None, uuid=None):  
        """ResultUUID - a model defined in OpenAPI

        :param result: The result of this ResultUUID.  
        :type result: str
        :param uuid: The uuid of this ResultUUID.  
        :type uuid: str
        """
        self.types = {
            'result': str,
            'uuid': str
        }

        self.attribute_map = {
            'result': 'result',
            'uuid': 'uuid'
        }

        self._result = result
        self._uuid = uuid

    @classmethod
    def from_dict(cls, dikt) -> 'ResultUUID':
        """Returns the dict as a model

        :param dikt: A dict.
        :type: dict
        :return: The inline_response_200 of this ResultUUID.  
        :rtype: ResultUUID
        """
        return util.deserialize_model(dikt, cls)

    @property
    def result(self):
        """Gets the result of this ResultUUID.

        Should respond with `found` or 404.  

        :return: The result of this ResultUUID.
        :rtype: str
        """
        return self._result

    @result.setter
    def result(self, result):
        """Sets the result of this ResultUUID.

        Should respond with `found` or 404.  

        :param result: The result of this ResultUUID.
        :type result: str
        """

        self._result = result

    @property
    def uuid(self):
        """Gets the uuid of this ResultUUID.

        Unique identifier (which may be the sha256 hash)  

        :return: The uuid of this ResultUUID.
        :rtype: str
        """
        return self._uuid

    @uuid.setter
    def uuid(self, uuid):
        """Sets the uuid of this ResultUUID.

        Unique identifier (which may be the sha256 hash)  

        :param uuid: The uuid of this ResultUUID.
        :type uuid: str
        """

        self._uuid = uuid
