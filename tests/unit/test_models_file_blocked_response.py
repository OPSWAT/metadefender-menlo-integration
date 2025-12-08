import unittest
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_blocked_response import FileBlockedResponse

class TestFileBlockedResponse(unittest.TestCase):

    def setUp(self):
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
        self.assertEqual(self.file_blocked_response.result, "pending")
        self.assertEqual(self.file_blocked_response.outcome, "clean")
        self.assertEqual(self.file_blocked_response.report_url, "https://example.com/report")
        self.assertEqual(self.file_blocked_response.filename, "example.txt")
        self.assertEqual(self.file_blocked_response.modifications, ["scanned", "sanitized"])
        self.assertEqual(self.file_blocked_response.outcome_categorization, "malware")
        self.assertEqual(self.file_blocked_response.observed_type, ["virus"])
        self.assertEqual(self.file_blocked_response.observed_specifics, ["suspicious behavior"])

    def test_property_setters_with_validation(self):
        test_cases = [
            ('result', 'completed', None),
            ('result', 'invalid_result', ValueError),
            ('outcome', 'infected', None),
            ('outcome', 'invalid_outcome', ValueError),
            ('report_url', 'https://example.com/new_report', None),
            ('report_url', None, ValueError),
            ('filename', 'new_example.txt', None),
            ('modifications', ['modified'], None),
            ('outcome_categorization', 'adware', None),
            ('observed_type', ['trojan'], None),
            ('observed_specifics', ['data theft'], None)
        ]
        
        for property_name, value, expected_exception in test_cases:
            if expected_exception:
                with self.assertRaises(expected_exception):
                    setattr(self.file_blocked_response, property_name, value)
            else:
                setattr(self.file_blocked_response, property_name, value)
                self.assertEqual(getattr(self.file_blocked_response, property_name), value)


if __name__ == '__main__':
    unittest.main()