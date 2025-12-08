import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_analysis_response import FileAnalysisResponse

class TestFileAnalysisResponse(unittest.TestCase):

    def setUp(self):
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
        self.assertEqual(self.file_analysis.result, self.result)
        self.assertEqual(self.file_analysis.outcome, self.outcome)
        self.assertEqual(self.file_analysis.report_url, self.report_url)
        self.assertEqual(self.file_analysis.filename, self.filename)
        self.assertEqual(self.file_analysis.modifications, self.modifications)

    def test_property_setters_with_validation(self):
        test_cases = [
            ('result', 'completed', None),
            ('result', 'invalid_status', ValueError),
            ('outcome', 'infected', None),
            ('outcome', 'unknown_status', ValueError),
            ('report_url', 'https://example.com/new_report', None),
            ('report_url', None, ValueError),
            ('filename', 'new_file.txt', None),
            ('modifications', ['modified', 'scanned'], None)
        ]
        
        for property_name, value, expected_exception in test_cases:
            if expected_exception:
                with self.assertRaises(expected_exception):
                    setattr(self.file_analysis, property_name, value)
            else:
                setattr(self.file_analysis, property_name, value)
                self.assertEqual(getattr(self.file_analysis, property_name), value)


if __name__ == '__main__':
    unittest.main()