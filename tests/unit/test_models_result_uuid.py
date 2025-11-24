import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.result_uuid import ResultUUID

class TestResultUUID(unittest.TestCase):

    def setUp(self):
        self.result_uuid = ResultUUID(
            result="found",
            uuid="abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz"
        )

    def test_initialization(self):
        self.assertEqual(self.result_uuid.result, "found")
        self.assertEqual(self.result_uuid.uuid, "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz")

    def test_property_setters(self):
        test_cases = [
            ('result', 'not found'),
            ('uuid', 'newuuid1234567890')
        ]
        
        for property_name, value in test_cases:
            setattr(self.result_uuid, property_name, value)
            self.assertEqual(getattr(self.result_uuid, property_name), value)

    def test_from_dict(self):
        data = {
            "result": "found",
            "uuid": "1234abcd5678efgh9012ijkl3456mnopqrst7890uvwx"
        }
        result_uuid_obj = ResultUUID.from_dict(data)
        self.assertEqual(result_uuid_obj.result, "found")
        self.assertEqual(result_uuid_obj.uuid, "1234abcd5678efgh9012ijkl3456mnopqrst7890uvwx")


if __name__ == '__main__':
    unittest.main()