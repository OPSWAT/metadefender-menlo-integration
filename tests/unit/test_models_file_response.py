import unittest

import os
import sys
import logging
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_response import FileResponse

class TestFileResponse(unittest.TestCase):
    def setUp(self):
        """Set up a valid instance of FileResponse for testing."""
        self.file_response = FileResponse(
            result="pending",
            outcome="clean",
            report_url="https://example.com/report",
            filename="example.txt"
        )

    def test_initialization(self):
        """Test that the instance initializes correctly."""
        self.assertEqual(self.file_response.result, "pending")
        self.assertEqual(self.file_response.outcome, "clean")
        self.assertEqual(self.file_response.report_url, "https://example.com/report")
        self.assertEqual(self.file_response.filename, "example.txt")

    def test_result_setter_valid(self):
        """Test setting a valid result."""
        self.file_response.result = "completed"
        self.assertEqual(self.file_response.result, "completed")

    def test_result_setter_invalid(self):
        """Test setting an invalid result."""
        with self.assertRaises(ValueError):
            self.file_response.result = "invalid_result"

    def test_outcome_setter_valid(self):
        """Test setting a valid outcome."""
        self.file_response.outcome = "infected"
        self.assertEqual(self.file_response.outcome, "infected")

    def test_outcome_setter_invalid(self):
        """Test setting an invalid outcome."""
        with self.assertRaises(ValueError):
            self.file_response.outcome = "invalid_outcome"

    def test_report_url_setter_valid(self):
        """Test setting a valid report URL."""
        self.file_response.report_url = "https://example.com/new_report"
        self.assertEqual(self.file_response.report_url, "https://example.com/new_report")

    def test_report_url_setter_invalid_none(self):
        """Test setting report URL to None."""
        with self.assertRaises(ValueError):
            self.file_response.report_url = None

    def test_filename_setter(self):
        """Test setting the filename."""
        self.file_response.filename = "new_example.txt"
        self.assertEqual(self.file_response.filename, "new_example.txt")

    def test_from_dict(self):
        """Test the from_dict method to create an object from a dictionary."""
        data = {
            "result": "completed",
            "outcome": "infected",
            "report_url": "https://example.com/infected_report",
            "filename": "infected_file.txt"
        }
        file_response_obj = FileResponse.from_dict(data)
        self.assertEqual(file_response_obj.result, "completed")
        self.assertEqual(file_response_obj.outcome, "infected")
        self.assertEqual(file_response_obj.report_url, "https://example.com/infected_report")
        self.assertEqual(file_response_obj.filename, "infected_file.txt")

if __name__ == '__main__':
    unittest.main()
