import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.result_uuid import ResultUUID

class TestResultUUID(unittest.TestCase):

    def setUp(self):
        """Set up a valid instance of ResultUUID for testing."""
        self.result_uuid = ResultUUID(
            result="found",
            uuid="abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz"
        )

    def test_initialization(self):
        """Test that the instance initializes correctly."""
        self.assertEqual(self.result_uuid.result, "found")
        self.assertEqual(self.result_uuid.uuid, "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz")

    def test_result_setter(self):
        """Test setting the result property."""
        self.result_uuid.result = "not found"
        self.assertEqual(self.result_uuid.result, "not found")

    def test_uuid_setter(self):
        """Test setting the uuid property."""
        self.result_uuid.uuid = "newuuid1234567890"
        self.assertEqual(self.result_uuid.uuid, "newuuid1234567890")

    def test_from_dict(self):
        """Test the from_dict method to create an object from a dictionary."""
        data = {
            "result": "found",
            "uuid": "1234abcd5678efgh9012ijkl3456mnopqrst7890uvwx"
        }
        result_uuid_obj = ResultUUID.from_dict(data)
        self.assertEqual(result_uuid_obj.result, "found")
        self.assertEqual(result_uuid_obj.uuid, "1234abcd5678efgh9012ijkl3456mnopqrst7890uvwx")

if __name__ == '__main__':
    unittest.main()
