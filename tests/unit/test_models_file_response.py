import unittest
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.file_response import FileResponse

class TestFileResponse(unittest.TestCase):

    def setUp(self):
        self.file_response = FileResponse(
            result="pending",
            outcome="clean",
            report_url="https://example.com/report",
            filename="example.txt"
        )

    def test_initialization(self):
        self.assertEqual(self.file_response.result, "pending")
        self.assertEqual(self.file_response.outcome, "clean")
        self.assertEqual(self.file_response.report_url, "https://example.com/report")
        self.assertEqual(self.file_response.filename, "example.txt")

    def test_property_setters_with_validation(self):
        test_cases = [
            ('result', 'completed', None),
            ('result', 'invalid_result', ValueError),
            ('outcome', 'infected', None),
            ('outcome', 'invalid_outcome', ValueError),
            ('report_url', 'https://example.com/new_report', None),
            ('report_url', None, ValueError),
            ('filename', 'new_example.txt', None)
        ]
        
        for property_name, value, expected_exception in test_cases:
            if expected_exception:
                with self.assertRaises(expected_exception):
                    setattr(self.file_response, property_name, value)
            else:
                setattr(self.file_response, property_name, value)
                self.assertEqual(getattr(self.file_response, property_name), value)

    def test_from_dict(self):
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