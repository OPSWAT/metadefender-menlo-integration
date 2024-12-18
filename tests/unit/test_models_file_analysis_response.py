import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse

class TestFileAnalysisResponse(unittest.TestCase):

    def setUp(self):
        """Set up test cases with initial parameters."""
        self.result = "pending"
        self.outcome = "clean"
        self.report_url = "https://example.com/report"
        self.filename = "sample_file.txt"
        self.modifications = ["modified"]

        self.file_analysis = FileAnalysisResponse(
            result=self.result,
            outcome=self.outcome,
            report_url=self.report_url,
            filename=self.filename,
            modifications=self.modifications
        )

    def test_initialization(self):
        """Test object initialization with default values."""
        self.assertEqual(self.file_analysis.result, self.result)
        self.assertEqual(self.file_analysis.outcome, self.outcome)
        self.assertEqual(self.file_analysis.report_url, self.report_url)
        self.assertEqual(self.file_analysis.filename, self.filename)
        self.assertEqual(self.file_analysis.modifications, self.modifications)

    def test_result_setter(self):
        """Test the setter for 'result' with valid and invalid values."""
        self.file_analysis.result = "completed"
        self.assertEqual(self.file_analysis.result, "completed")

        with self.assertRaises(ValueError):
            self.file_analysis.result = "invalid_status"

    def test_outcome_setter(self):
        """Test the setter for 'outcome' with valid and invalid values."""
        self.file_analysis.outcome = "infected"
        self.assertEqual(self.file_analysis.outcome, "infected")

        with self.assertRaises(ValueError):
            self.file_analysis.outcome = "unknown_status"

    def test_report_url_setter(self):
        """Test the setter for 'report_url'."""
        self.file_analysis.report_url = "https://example.com/new_report"
        self.assertEqual(self.file_analysis.report_url, "https://example.com/new_report")

        with self.assertRaises(ValueError):
            self.file_analysis.report_url = None  # Should raise ValueError for None

    def test_filename_setter(self):
        """Test the setter for 'filename'."""
        self.file_analysis.filename = "new_file.txt"
        self.assertEqual(self.file_analysis.filename, "new_file.txt")

    def test_modifications_setter(self):
        """Test the setter for 'modifications'."""
        new_modifications = ["modified", "scanned"]
        self.file_analysis.modifications = new_modifications
        self.assertEqual(self.file_analysis.modifications, new_modifications)

if __name__ == '__main__':
    unittest.main()
