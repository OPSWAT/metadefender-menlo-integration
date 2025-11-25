import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_blocked_error import FileBlockedError

class TestFileBlockedError(unittest.TestCase):

    def setUp(self):
        self.file_blocked_error = FileBlockedError(
            result="pending",
            outcome="clean",
            report_url="https://example.com/report",
            filename="example.txt",
            error_message="No errors"
        )

    def test_initialization(self):
        self.assertEqual(self.file_blocked_error.result, "pending")
        self.assertEqual(self.file_blocked_error.outcome, "clean")
        self.assertEqual(self.file_blocked_error.report_url, "https://example.com/report")
        self.assertEqual(self.file_blocked_error.filename, "example.txt")
        self.assertEqual(self.file_blocked_error.error_message, "No errors")

    def test_property_setters_with_validation(self):
        test_cases = [
            ('result', 'completed', None),
            ('result', 'invalid_result', ValueError),
            ('outcome', 'infected', None),
            ('outcome', 'invalid_outcome', ValueError),
            ('report_url', 'https://example.com/new_report', None),
            ('report_url', None, ValueError),
            ('filename', 'new_example.txt', None),
            ('error_message', 'New error message', None)
        ]
        
        for property_name, value, expected_exception in test_cases:
            if expected_exception:
                with self.assertRaises(expected_exception):
                    setattr(self.file_blocked_error, property_name, value)
            else:
                setattr(self.file_blocked_error, property_name, value)
                self.assertEqual(getattr(self.file_blocked_error, property_name), value)

    def test_from_dict(self):
        data = {
            "result": "completed",
            "outcome": "error",
            "report_url": "https://example.com/error_report",
            "filename": "error_file.txt",
            "error_message": "File blocked due to a virus"
        }
        file_blocked_error_obj = FileBlockedError.from_dict(data)
        self.assertEqual(file_blocked_error_obj.result, "completed")
        self.assertEqual(file_blocked_error_obj.outcome, "error")
        self.assertEqual(file_blocked_error_obj.report_url, "https://example.com/error_report")
        self.assertEqual(file_blocked_error_obj.filename, "error_file.txt")
        self.assertEqual(file_blocked_error_obj.error_message, "File blocked due to a virus")


if __name__ == '__main__':
    unittest.main()