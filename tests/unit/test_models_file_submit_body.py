import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_submit_body import FileSubmitBody

class TestFileSubmitBody(unittest.TestCase):

    def setUp(self):
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
        self.assertEqual(self.file_submit_body.userid, "user123")
        self.assertEqual(self.file_submit_body.srcuri, "https://example.com/source")
        self.assertEqual(self.file_submit_body.clientip, "192.0.2.1")
        self.assertEqual(self.file_submit_body.sha256, "abcd1234efgh5678ijkl9012mnop3456qrst7890uvwx1234yz")
        self.assertEqual(self.file_submit_body.filename, "example.txt")
        self.assertEqual(self.file_submit_body.file_type, "text/plain")
        self.assertEqual(self.file_submit_body.filesize, 1024)

    def test_property_setters(self):
        test_cases = [
            ('userid', 'user456'),
            ('srcuri', 'https://example.com/new_source'),
            ('clientip', '198.51.100.1'),
            ('sha256', 'newhash1234567890'),
            ('filename', 'new_example.txt'),
            ('file_type', 'text/csv'),
            ('filesize', 2048)
        ]
        
        for property_name, value in test_cases:
            setattr(self.file_submit_body, property_name, value)
            self.assertEqual(getattr(self.file_submit_body, property_name), value)

    def test_from_dict(self):
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