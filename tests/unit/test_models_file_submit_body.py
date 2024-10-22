import unittest

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_submit_body import FileSubmitBody

class TestFileSubmitBody(unittest.TestCase):

    def setUp(self):
        """Set up a valid instance of FileSubmitBody for testing."""
        self.file_submit_body = FileSubmitBody(
            userid="user123",
            srcuri="https://example.com/source",
            clientip="192.0.2.1",
            sha256="abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz",
            filename="example.txt",
            file_type="text/plain",
            filesize=1024
        )

    def test_initialization(self):
        """Test that the instance initializes correctly."""
        self.assertEqual(self.file_submit_body.userid, "user123")
        self.assertEqual(self.file_submit_body.srcuri, "https://example.com/source")
        self.assertEqual(self.file_submit_body.clientip, "192.0.2.1")
        self.assertEqual(self.file_submit_body.sha256, "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz")
        self.assertEqual(self.file_submit_body.filename, "example.txt")
        self.assertEqual(self.file_submit_body.file_type, "text/plain")
        self.assertEqual(self.file_submit_body.filesize, 1024)

    def test_userid_setter(self):
        """Test setting the userid property."""
        self.file_submit_body.userid = "user456"
        self.assertEqual(self.file_submit_body.userid, "user456")

    def test_srcuri_setter(self):
        """Test setting the srcuri property."""
        self.file_submit_body.srcuri = "https://example.com/new_source"
        self.assertEqual(self.file_submit_body.srcuri, "https://example.com/new_source")

    def test_clientip_setter(self):
        """Test setting the clientip property."""
        self.file_submit_body.clientip = "198.51.100.1"
        self.assertEqual(self.file_submit_body.clientip, "198.51.100.1")

    def test_sha256_setter(self):
        """Test setting the sha256 property."""
        self.file_submit_body.sha256 = "newhash1234567890"
        self.assertEqual(self.file_submit_body.sha256, "newhash1234567890")

    def test_filename_setter(self):
        """Test setting the filename property."""
        self.file_submit_body.filename = "new_example.txt"
        self.assertEqual(self.file_submit_body.filename, "new_example.txt")

    def test_file_type_setter(self):
        """Test setting the file_type property."""
        self.file_submit_body.file_type = "text/csv"
        self.assertEqual(self.file_submit_body.file_type, "text/csv")

    def test_filesize_setter(self):
        """Test setting the filesize property."""
        self.file_submit_body.filesize = 2048
        self.assertEqual(self.file_submit_body.filesize, 2048)

    def test_from_dict(self):
        """Test the from_dict method to create an object from a dictionary."""
        data = {
            "userid": "user789",
            "srcuri": "https://example.com/another_source",
            "clientip": "203.0.113.1",
            "sha256": "1234abcd5678efgh9012ijkl3456mnop7890qrst",
            "filename": "another_example.txt",
            "file_type": "image/png",
            "filesize": 2048
        }
        file_submit_body_obj = FileSubmitBody.from_dict(data)
        self.assertEqual(file_submit_body_obj.userid, "user789")
        self.assertEqual(file_submit_body_obj.srcuri, "https://example.com/another_source")
        self.assertEqual(file_submit_body_obj.clientip, "203.0.113.1")
        self.assertEqual(file_submit_body_obj.sha256, "1234abcd5678efgh9012ijkl3456mnop7890qrst")
        self.assertEqual(file_submit_body_obj.filename, "another_example.txt")
        self.assertEqual(file_submit_body_obj.file_type, "image/png")
        self.assertEqual(file_submit_body_obj.filesize, 2048)

if __name__ == '__main__':
    unittest.main()
