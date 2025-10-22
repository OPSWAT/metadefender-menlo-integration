import unittest
from unittest.mock import patch, Mock
import datetime
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api import util


class TestUtil(unittest.TestCase):

    def test_deserialize_scenarios(self):
        test_cases = [
            (None, str, None),
            (123, int, 123),
            ("test", str, "test"),
            (3.14, float, 3.14),
            (True, bool, True),
            (b"bytes", bytearray, b"bytes"),
            ({"key": "value"}, object, {"key": "value"})
        ]
        
        for data, klass, expected in test_cases:
            with self.subTest(data=data, klass=klass):
                result = util._deserialize(data, klass)
                if expected is None:
                    self.assertIsNone(result)
                else:
                    self.assertEqual(result, expected)

    def test_deserialize_date_scenarios(self):
        test_cases = [
            ("2023-01-01", datetime.date),
            ("2023-12-31", datetime.date)
        ]
        
        for date_string, expected_type in test_cases:
            with self.subTest(date_string=date_string):
                result = util._deserialize(date_string, datetime.date)
                self.assertIsInstance(result, expected_type)

    def test_deserialize_datetime_scenarios(self):
        test_cases = [
            ("2023-01-01T10:30:00", datetime.datetime),
            ("2023-12-31T23:59:59", datetime.datetime)
        ]
        
        for datetime_string, expected_type in test_cases:
            with self.subTest(datetime_string=datetime_string):
                result = util._deserialize(datetime_string, datetime.datetime)
                self.assertIsInstance(result, expected_type)

    def test_deserialize_primitive_scenarios(self):
        test_cases = [
            ("123", int, 123),
            (123, str, "123"),
            ("3.14", float, 3.14),
            (True, bool, True),
            (False, bool, False)
        ]
        
        for data, klass, expected in test_cases:
            with self.subTest(data=data, klass=klass):
                result = util._deserialize_primitive(data, klass)
                self.assertEqual(result, expected)

    def test_deserialize_primitive_exception_scenarios(self):
        with patch('six.u') as mock_u:
            mock_u.return_value = "unicode_string"
            
            mock_klass = Mock()
            mock_klass.side_effect = UnicodeEncodeError('utf-8', 'test', 0, 1, 'error')
            
            result = util._deserialize_primitive("test", mock_klass)
            self.assertEqual(result, "unicode_string")

        mock_klass = Mock()
        mock_klass.side_effect = TypeError("Cannot convert")
        
        result = util._deserialize_primitive("test", mock_klass)
        self.assertEqual(result, "test")

    def test_deserialize_object_scenarios(self):
        test_cases = ["string", 123, {"key": "value"}, [1, 2, 3], None]
        
        for value in test_cases:
            with self.subTest(value=value):
                result = util._deserialize_object(value)
                self.assertEqual(result, value)

    def test_deserialize_date_method_scenarios(self):
        with patch('dateutil.parser.parse') as mock_parse:
            mock_date = datetime.date(2023, 1, 1)
            mock_parse.return_value.date.return_value = mock_date
            
            result = util.deserialize_date("2023-01-01")
            self.assertEqual(result, mock_date)
            mock_parse.assert_called_once_with("2023-01-01")

        with patch('dateutil.parser.parse', side_effect=ImportError):
            result = util.deserialize_date("2023-01-01")
            self.assertEqual(result, "2023-01-01")

    def test_deserialize_datetime_method_scenarios(self):
        with patch('dateutil.parser.parse') as mock_parse:
            mock_datetime = datetime.datetime(2023, 1, 1, 10, 30, 0)
            mock_parse.return_value = mock_datetime
            
            result = util.deserialize_datetime("2023-01-01T10:30:00")
            self.assertEqual(result, mock_datetime)
            mock_parse.assert_called_once_with("2023-01-01T10:30:00")

        with patch('dateutil.parser.parse', side_effect=ImportError):
            result = util.deserialize_datetime("2023-01-01T10:30:00")
            self.assertEqual(result, "2023-01-01T10:30:00")

    def test_deserialize_model_scenarios(self):
        mock_model = Mock()
        mock_model.types = {'field1': str, 'field2': int}
        mock_model.attribute_map = {'field1': 'field1', 'field2': 'field2'}
        
        test_cases = [
            ({'field1': 'test', 'field2': 123}, True, 2),
            ({'field1': 'test'}, True, 1),
            ({}, True, 0),
            ({'field1': 'test', 'field2': 123}, False, 0)
        ]
        
        for data, has_types, expected_calls in test_cases:
            with self.subTest(data=data, has_types=has_types):
                mock_model.types = mock_model.types if has_types else None
                
                with patch.object(util, '_deserialize') as mock_deserialize:
                    mock_deserialize.return_value = "deserialized_value"
                    
                    result = util.deserialize_model(data, lambda: mock_model)
                    
                    if has_types:
                        self.assertEqual(mock_deserialize.call_count, expected_calls)
                    else:
                        self.assertEqual(result, data)

    def test_deserialize_model_edge_cases(self):
        mock_model = Mock()
        mock_model.types = {'field1': str}
        mock_model.attribute_map = {'field1': 'field1'}
        
        result = util.deserialize_model(None, lambda: mock_model)
        self.assertIsInstance(result, Mock)

        result = util.deserialize_model("string_data", lambda: mock_model)
        self.assertIsInstance(result, Mock)

    def test_deserialize_list_scenarios(self):
        test_cases = [
            ([1, 2, 3], int, 3),
            (["a", "b", "c"], str, 3),
            ([], int, 0)
        ]
        
        for data, boxed_type, expected_calls in test_cases:
            with self.subTest(data=data, boxed_type=boxed_type):
                with patch.object(util, '_deserialize') as mock_deserialize:
                    mock_deserialize.return_value = "deserialized"
                    
                    result = util._deserialize_list(data, boxed_type)
                    
                    self.assertEqual(len(result), len(data))
                    self.assertEqual(mock_deserialize.call_count, expected_calls)

    def test_deserialize_dict_scenarios(self):
        test_cases = [
            ({'a': 1, 'b': 2}, int, 2),
            ({'x': 'test', 'y': 'data'}, str, 2),
            ({}, int, 0)
        ]
        
        for data, boxed_type, expected_calls in test_cases:
            with self.subTest(data=data, boxed_type=boxed_type):
                with patch.object(util, '_deserialize') as mock_deserialize:
                    mock_deserialize.return_value = "deserialized"
                    
                    result = util._deserialize_dict(data, boxed_type)
                    
                    self.assertEqual(len(result), len(data))
                    self.assertEqual(mock_deserialize.call_count, expected_calls)

    def test_type_check_scenarios(self):
        mock_dict_type = Mock()
        mock_dict_type.__extra__ = dict
        
        mock_list_type = Mock()
        mock_list_type.__extra__ = list
        
        test_cases = [
            (mock_dict_type, True, False),
            (mock_list_type, False, True),
            (str, False, False),
            (int, False, False)
        ]
        
        for klass, is_dict_expected, is_list_expected in test_cases:
            with self.subTest(klass=klass):
                if hasattr(klass, '__extra__'):
                    dict_result = util.is_dict(klass)
                    list_result = util.is_list(klass)
                    self.assertEqual(dict_result, is_dict_expected)
                    self.assertEqual(list_result, is_list_expected)
                else:
                    self.assertFalse(is_dict_expected)
                    self.assertFalse(is_list_expected)

    def test_deserialize_generic_types_scenarios(self):
        mock_list_type = Mock()
        mock_list_type.__args__ = [str]
        mock_list_type.__extra__ = list
        
        mock_dict_type = Mock()
        mock_dict_type.__args__ = [str, int]
        mock_dict_type.__extra__ = dict
        
        test_cases = [
            (["a", "b"], mock_list_type, True, False),
            ({'a': 1, 'b': 2}, mock_dict_type, False, True)
        ]
        
        for data, klass, is_list, is_dict in test_cases:
            with self.subTest(data=data, klass=klass):
                with patch.object(util, 'is_generic', return_value=True), \
                     patch.object(util, 'is_list', return_value=is_list), \
                     patch.object(util, 'is_dict', return_value=is_dict), \
                     patch.object(util, '_deserialize_list') as mock_deserialize_list, \
                     patch.object(util, '_deserialize_dict') as mock_deserialize_dict, \
                     patch.object(util, 'deserialize_model') as mock_deserialize_model:
                    
                    mock_deserialize_list.return_value = "list_result"
                    mock_deserialize_dict.return_value = "dict_result"
                    mock_deserialize_model.return_value = "model_result"
                    
                    result = util._deserialize(data, klass)
                    
                    if is_list:
                        mock_deserialize_list.assert_called_once()
                        self.assertEqual(result, "list_result")
                    elif is_dict:
                        mock_deserialize_dict.assert_called_once()
                        self.assertEqual(result, "dict_result")
                    else:
                        mock_deserialize_model.assert_called_once()
                        self.assertEqual(result, "model_result")


if __name__ == '__main__':
    unittest.main()
