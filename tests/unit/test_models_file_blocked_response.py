import unittest
from metadefender_menlo.api.models.file_blocked_response import FileBlockedResponse

class TestFileBlockedResponse(unittest.TestCase):

    def setUp(self):
        """Set up a valid instance of FileBlockedResponse for testing."""
        self.file_blocked_response = FileBlockedResponse(
            result="pending",
            outcome="clean",
            report_url="https://example.com/report",
            filename="example.txt",
            modifications=["scanned", "sanitized"],
            outcome_categorization="malware",
            observed_type=["virus"],
            observed_specifics=["suspicious behavior"]
        )

    def test_initialization(self):
        """Test that the instance initializes correctly."""
        self.assertEqual(self.file_blocked_response.result, "pending")
        self.assertEqual(self.file_blocked_response.outcome, "clean")
        self.assertEqual(self.file_blocked_response.report_url, "https://example.com/report")
        self.assertEqual(self.file_blocked_response.filename, "example.txt")
        self.assertEqual(self.file_blocked_response.modifications, ["scanned", "sanitized"])
        self.assertEqual(self.file_blocked_response.outcome_categorization, "malware")
        self.assertEqual(self.file_blocked_response.observed_type, ["virus"])
        self.assertEqual(self.file_blocked_response.observed_specifics, ["suspicious behavior"])

    def test_result_setter_valid(self):
        """Test setting a valid result."""
        self.file_blocked_response.result = "completed"
        self.assertEqual(self.file_blocked_response.result, "completed")

    def test_result_setter_invalid(self):
        """Test setting an invalid result."""
        with self.assertRaises(ValueError):
            self.file_blocked_response.result = "invalid_result"

    def test_outcome_setter_valid(self):
        """Test setting a valid outcome."""
        self.file_blocked_response.outcome = "infected"
        self.assertEqual(self.file_blocked_response.outcome, "infected")

    def test_outcome_setter_invalid(self):
        """Test setting an invalid outcome."""
        with self.assertRaises(ValueError):
            self.file_blocked_response.outcome = "invalid_outcome"

    def test_report_url_setter_valid(self):
        """Test setting a valid report URL."""
        self.file_blocked_response.report_url = "https://example.com/new_report"
        self.assertEqual(self.file_blocked_response.report_url, "https://example.com/new_report")

    def test_report_url_setter_invalid_none(self):
        """Test setting report URL to None."""
        with self.assertRaises(ValueError):
            self.file_blocked_response.report_url = None

    def test_filename_setter(self):
        """Test setting the filename."""
        self.file_blocked_response.filename = "new_example.txt"
        self.assertEqual(self.file_blocked_response.filename, "new_example.txt")

    def test_modifications_setter(self):
        """Test setting modifications."""
        self.file_blocked_response.modifications = ["modified"]
        self.assertEqual(self.file_blocked_response.modifications, ["modified"])

    def test_outcome_categorization_setter(self):
        """Test setting the outcome categorization."""
        self.file_blocked_response.outcome_categorization = "adware"
        self.assertEqual(self.file_blocked_response.outcome_categorization, "adware")

    def test_observed_type_setter(self):
        """Test setting the observed type."""
        self.file_blocked_response.observed_type = ["trojan"]
        self.assertEqual(self.file_blocked_response.observed_type, ["trojan"])

    def test_observed_specifics_setter(self):
        """Test setting the observed specifics."""
        self.file_blocked_response.observed_specifics = ["data theft"]
        self.assertEqual(self.file_blocked_response.observed_specifics, ["data theft"])

if __name__ == '__main__':
    unittest.main()
