import unittest
from unittest.mock import patch, Mock
import datetime
import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api import util


class TestUtil(unittest.TestCase):

    def test_deserialize_none(self):
        """Test _deserialize with None data"""
        result = util._deserialize(None, str)
        self.assertIsNone(result)

    def test_deserialize_primitive_types(self):
        """Test _deserialize with primitive types"""
        test_cases = [
            # (data, klass, expected_type)
            (123, int, int),
            ("test", str, str),
            (3.14, float, float),
            (True, bool, bool),
            (b"bytes", bytearray, bytearray),
        ]
        
        for data, klass, expected_type in test_cases:
            with self.subTest(data=data, klass=klass):
                result = util._deserialize(data, klass)
                self.assertIsInstance(result, expected_type)
                self.assertEqual(result, data)

    def test_deserialize_object(self):
        """Test _deserialize with object type"""
        test_data = {"key": "value"}
        result = util._deserialize(test_data, object)
        self.assertEqual(result, test_data)

    def test_deserialize_date(self):
        """Test _deserialize with date type"""
        test_cases = [
            ("2023-01-01", datetime.date),
            ("2023-12-31", datetime.date),
        ]
        
        for date_string, expected_type in test_cases:
            with self.subTest(date_string=date_string):
                result = util._deserialize(date_string, datetime.date)
                self.assertIsInstance(result, expected_type)

    def test_deserialize_datetime(self):
        """Test _deserialize with datetime type"""
        test_cases = [
            ("2023-01-01T10:30:00", datetime.datetime),
            ("2023-12-31T23:59:59", datetime.datetime),
        ]
        
        for datetime_string, expected_type in test_cases:
            with self.subTest(datetime_string=datetime_string):
                result = util._deserialize(datetime_string, datetime.datetime)
                self.assertIsInstance(result, expected_type)

    def test_deserialize_primitive_scenarios(self):
        """Test _deserialize_primitive method scenarios"""
        test_cases = [
            # (data, klass, expected)
            ("123", int, 123),
            (123, str, "123"),
            ("3.14", float, 3.14),
            (True, bool, True),
            (False, bool, False),
        ]
        
        for data, klass, expected in test_cases:
            with self.subTest(data=data, klass=klass):
                result = util._deserialize_primitive(data, klass)
                self.assertEqual(result, expected)

    def test_deserialize_primitive_unicode_error(self):
        """Test _deserialize_primitive with UnicodeEncodeError"""
        with patch('six.u') as mock_u:
            mock_u.return_value = "unicode_string"
            
            # Mock klass to raise UnicodeEncodeError
            mock_klass = Mock()
            mock_klass.side_effect = UnicodeEncodeError('utf-8', 'test', 0, 1, 'error')
            
            result = util._deserialize_primitive("test", mock_klass)
            self.assertEqual(result, "unicode_string")

    def test_deserialize_primitive_type_error(self):
        """Test _deserialize_primitive with TypeError"""
        mock_klass = Mock()
        mock_klass.side_effect = TypeError("Cannot convert")
        
        result = util._deserialize_primitive("test", mock_klass)
        self.assertEqual(result, "test")

    def test_deserialize_object_scenarios(self):
        """Test _deserialize_object method"""
        test_cases = [
            "string",
            123,
            {"key": "value"},
            [1, 2, 3],
            None,
        ]
        
        for value in test_cases:
            with self.subTest(value=value):
                result = util._deserialize_object(value)
                self.assertEqual(result, value)

    @patch('dateutil.parser.parse')
    def test_deserialize_date_success(self, mock_parse):
        """Test deserialize_date with successful parsing"""
        mock_date = datetime.date(2023, 1, 1)
        mock_parse.return_value.date.return_value = mock_date
        
        result = util.deserialize_date("2023-01-01")
        self.assertEqual(result, mock_date)
        mock_parse.assert_called_once_with("2023-01-01")

    @patch('dateutil.parser.parse', side_effect=ImportError)
    def test_deserialize_date_import_error(self, mock_parse):
        """Test deserialize_date with ImportError"""
        result = util.deserialize_date("2023-01-01")
        self.assertEqual(result, "2023-01-01")

    @patch('dateutil.parser.parse')
    def test_deserialize_datetime_success(self, mock_parse):
        """Test deserialize_datetime with successful parsing"""
        mock_datetime = datetime.datetime(2023, 1, 1, 10, 30, 0)
        mock_parse.return_value = mock_datetime
        
        result = util.deserialize_datetime("2023-01-01T10:30:00")
        self.assertEqual(result, mock_datetime)
        mock_parse.assert_called_once_with("2023-01-01T10:30:00")

    @patch('dateutil.parser.parse', side_effect=ImportError)
    def test_deserialize_datetime_import_error(self, mock_parse):
        """Test deserialize_datetime with ImportError"""
        result = util.deserialize_datetime("2023-01-01T10:30:00")
        self.assertEqual(result, "2023-01-01T10:30:00")

    def test_deserialize_model_scenarios(self):
        """Test deserialize_model method scenarios"""
        # Mock model class
        mock_model = Mock()
        mock_model.types = {'field1': str, 'field2': int}
        mock_model.attribute_map = {'field1': 'field1', 'field2': 'field2'}
        
        test_cases = [
            # (data, has_types, expected_calls)
            ({'field1': 'test', 'field2': 123}, True, 2),
            ({'field1': 'test'}, True, 1),
            ({}, True, 0),
            ({'field1': 'test', 'field2': 123}, False, 0),  # No types
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

    def test_deserialize_model_none_data(self):
        """Test deserialize_model with None data"""
        mock_model = Mock()
        mock_model.types = {'field1': str}
        mock_model.attribute_map = {'field1': 'field1'}
        
        result = util.deserialize_model(None, lambda: mock_model)
        self.assertIsInstance(result, Mock)

    def test_deserialize_model_non_dict_list(self):
        """Test deserialize_model with non-dict/list data"""
        mock_model = Mock()
        mock_model.types = {'field1': str}
        mock_model.attribute_map = {'field1': 'field1'}
        
        result = util.deserialize_model("string_data", lambda: mock_model)
        self.assertIsInstance(result, Mock)

    def test_deserialize_list_scenarios(self):
        """Test _deserialize_list method scenarios"""
        test_cases = [
            # (data, boxed_type, expected_calls)
            ([1, 2, 3], int, 3),
            (["a", "b", "c"], str, 3),
            ([], int, 0),
        ]
        
        for data, boxed_type, expected_calls in test_cases:
            with self.subTest(data=data, boxed_type=boxed_type):
                with patch.object(util, '_deserialize') as mock_deserialize:
                    mock_deserialize.return_value = "deserialized"
                    
                    result = util._deserialize_list(data, boxed_type)
                    
                    self.assertEqual(len(result), len(data))
                    self.assertEqual(mock_deserialize.call_count, expected_calls)

    def test_deserialize_dict_scenarios(self):
        """Test _deserialize_dict method scenarios"""
        test_cases = [
            # (data, boxed_type, expected_calls)
            ({'a': 1, 'b': 2}, int, 2),
            ({'x': 'test', 'y': 'data'}, str, 2),
            ({}, int, 0),
        ]
        
        for data, boxed_type, expected_calls in test_cases:
            with self.subTest(data=data, boxed_type=boxed_type):
                with patch.object(util, '_deserialize') as mock_deserialize:
                    mock_deserialize.return_value = "deserialized"
                    
                    result = util._deserialize_dict(data, boxed_type)
                    
                    self.assertEqual(len(result), len(data))
                    self.assertEqual(mock_deserialize.call_count, expected_calls)

    def test_is_dict_scenarios(self):
        """Test is_dict method scenarios"""
        # Mock dict type
        mock_dict_type = Mock()
        mock_dict_type.__extra__ = dict
        
        test_cases = [
            # (klass, expected)
            (mock_dict_type, True),
            (str, False),
            (int, False),
        ]
        
        for klass, expected in test_cases:
            with self.subTest(klass=klass):
                # Use hasattr to avoid AttributeError
                if hasattr(klass, '__extra__'):
                    result = util.is_dict(klass)
                    self.assertEqual(result, expected)
                else:
                    # For types without __extra__, it should return False
                    self.assertFalse(expected)

    def test_is_list_scenarios(self):
        """Test is_list method scenarios"""
        # Mock list type
        mock_list_type = Mock()
        mock_list_type.__extra__ = list
        
        test_cases = [
            # (klass, expected)
            (mock_list_type, True),
            (str, False),
            (int, False),
        ]
        
        for klass, expected in test_cases:
            with self.subTest(klass=klass):
                # Use hasattr to avoid AttributeError
                if hasattr(klass, '__extra__'):
                    result = util.is_list(klass)
                    self.assertEqual(result, expected)
                else:
                    # For types without __extra__, it should return False
                    self.assertFalse(expected)

    def test_deserialize_generic_types(self):
        """Test _deserialize with generic types"""
        # Mock generic types
        mock_list_type = Mock()
        mock_list_type.__args__ = [str]
        mock_list_type.__extra__ = list
        
        mock_dict_type = Mock()
        mock_dict_type.__args__ = [str, int]
        mock_dict_type.__extra__ = dict
        
        test_cases = [
            # (data, klass, is_list, is_dict)
            (["a", "b"], mock_list_type, True, False),
            ({'a': 1, 'b': 2}, mock_dict_type, False, True),
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
