import unittest
from unittest.mock import Mock, patch
import os
import sys

sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.base_model import Model


class TestModel(unittest.TestCase):

    def setUp(self):
        class SimpleModel(Model):
            types = {'name': str}
            attribute_map = {'name': 'full_name'}
        
        self.SimpleModel = SimpleModel

    def test_class_variables(self):
        self.assertEqual(Model.types, {})
        self.assertEqual(Model.attribute_map, {})

    @patch('metadefender_menlo.api.util.deserialize_model')
    def test_from_dict(self, mock_deserialize):
        mock_deserialize.return_value = 'test_result'
        result = self.SimpleModel.from_dict({'test': 'data'})
        self.assertEqual(result, 'test_result')
        mock_deserialize.assert_called_once_with({'test': 'data'}, self.SimpleModel)

    def test_to_dict_scenarios(self):
        test_cases = [
            ('simple', {'name': 'John'}, {'name': 'John'}),
            ('none', {'name': None}, {'name': None}),
            ('empty_types', {}, {})
        ]
        
        for test_type, instance_data, expected in test_cases:
            if test_type == 'empty_types':
                class EmptyModel(Model):
                    types = {}
                    attribute_map = {}
                instance = EmptyModel()
            else:
                instance = self.SimpleModel()
                for key, value in instance_data.items():
                    setattr(instance, key, value)
            
            result = instance.to_dict()
            self.assertEqual(result, expected)

    def test_to_dict_with_lists(self):
        class ListModel(Model):
            types = {'items': list}
            attribute_map = {'items': 'item_list'}
        
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {'serialized': 'object'}
        
        test_cases = [
            (['item1', 'item2'], {'items': ['item1', 'item2']}),
            ([mock_obj, 'string'], {'items': [{'serialized': 'object'}, 'string']})
        ]
        
        for items, expected in test_cases:
            instance = ListModel()
            instance.items = items
            result = instance.to_dict()
            self.assertEqual(result, expected)

    def test_to_dict_with_objects_and_dicts(self):
        class ObjectModel(Model):
            types = {'metadata': dict}
            attribute_map = {'metadata': 'meta_data'}
        
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {'serialized': 'object'}
        
        test_cases = [
            (mock_obj, {'metadata': {'serialized': 'object'}}),
            ({'key': 'value'}, {'metadata': {'key': 'value'}}),
            ({'key': mock_obj, 'simple': 'value'}, {'metadata': {'key': {'serialized': 'object'}, 'simple': 'value'}})
        ]
        
        for metadata, expected in test_cases:
            instance = ObjectModel()
            instance.metadata = metadata
            result = instance.to_dict()
            self.assertEqual(result, expected)

    def test_string_representations(self):
        instance = self.SimpleModel()
        instance.name = 'John'
        
        result_str = instance.to_str()
        result_repr = repr(instance)
        
        self.assertIsInstance(result_str, str)
        self.assertIsInstance(result_repr, str)
        self.assertIn('John', result_str)
        self.assertIn('John', result_repr)

    def test_equality_comparisons(self):
        instance1 = self.SimpleModel()
        instance1.name = 'John'
        instance2 = self.SimpleModel()
        instance2.name = 'John'
        
        self.assertEqual(instance1, instance2)

if __name__ == '__main__':
    unittest.main()