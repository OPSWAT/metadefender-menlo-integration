import unittest

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_blocked_error import FileBlockedError

class TestFileBlockedError(unittest.TestCase):

    def setUp(self):
        """Set up a valid instance of FileBlockedError for testing."""
        self.file_blocked_error = FileBlockedError(
            result="pending",
            outcome="clean",
            report_url="https://example.com/report",
            filename="example.txt",
            error_message="No errors"
        )

    def test_initialization(self):
        """Test that the instance initializes correctly."""
        self.assertEqual(self.file_blocked_error.result, "pending")
        self.assertEqual(self.file_blocked_error.outcome, "clean")
        self.assertEqual(self.file_blocked_error.report_url, "https://example.com/report")
        self.assertEqual(self.file_blocked_error.filename, "example.txt")
        self.assertEqual(self.file_blocked_error.error_message, "No errors")

    def test_result_setter_valid(self):
        """Test setting a valid result."""
        self.file_blocked_error.result = "completed"
        self.assertEqual(self.file_blocked_error.result, "completed")

    def test_result_setter_invalid(self):
        """Test setting an invalid result."""
        with self.assertRaises(ValueError):
            self.file_blocked_error.result = "invalid_result"

    def test_outcome_setter_valid(self):
        """Test setting a valid outcome."""
        self.file_blocked_error.outcome = "infected"
        self.assertEqual(self.file_blocked_error.outcome, "infected")

    def test_outcome_setter_invalid(self):
        """Test setting an invalid outcome."""
        with self.assertRaises(ValueError):
            self.file_blocked_error.outcome = "invalid_outcome"

    def test_report_url_setter_valid(self):
        """Test setting a valid report URL."""
        self.file_blocked_error.report_url = "https://example.com/new_report"
        self.assertEqual(self.file_blocked_error.report_url, "https://example.com/new_report")

    def test_report_url_setter_invalid_none(self):
        """Test setting report URL to None."""
        with self.assertRaises(ValueError):
            self.file_blocked_error.report_url = None

    def test_filename_setter(self):
        """Test setting the filename."""
        self.file_blocked_error.filename = "new_example.txt"
        self.assertEqual(self.file_blocked_error.filename, "new_example.txt")

    def test_error_message_setter(self):
        """Test setting the error message."""
        self.file_blocked_error.error_message = "New error message"
        self.assertEqual(self.file_blocked_error.error_message, "New error message")

    def test_from_dict(self):
        """Test the from_dict method to create an object from a dictionary."""
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
