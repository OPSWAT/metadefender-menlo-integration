import unittest
from unittest.mock import Mock, patch

import os
import sys
sys.path.insert(0, os.path.abspath('../mdcl-menlo-middleware'))
from metadefender_menlo.api.models.base_model import Model


class TestModel(unittest.TestCase):
    """Simple test suite for Model class with 90%+ coverage"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a simple test model class
        class SimpleModel(Model):
            types = {'name': str}
            attribute_map = {'name': 'full_name'}
        
        self.SimpleModel = SimpleModel

    def test_class_variables(self):
        """Test class variables - covers lines 14, 18"""
        self.assertEqual(Model.types, {})
        self.assertEqual(Model.attribute_map, {})

    @patch('metadefender_menlo.api.util.deserialize_model')
    def test_from_dict(self, mock_deserialize):
        """Test from_dict method - covers lines 20-23"""
        mock_deserialize.return_value = 'test_result'
        result = self.SimpleModel.from_dict({'test': 'data'})
        self.assertEqual(result, 'test_result')
        mock_deserialize.assert_called_once_with({'test': 'data'}, self.SimpleModel)

    def test_to_dict_simple(self):
        """Test to_dict with simple values - covers lines 25-50"""
        instance = self.SimpleModel()
        instance.name = 'John'
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'name': 'John'})

    def test_to_dict_none(self):
        """Test to_dict with None values - covers lines 25-50"""
        instance = self.SimpleModel()
        instance.name = None
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'name': None})

    def test_to_dict_with_list(self):
        """Test to_dict with list - covers lines 34-38"""
        class ListModel(Model):
            types = {'items': list}
            attribute_map = {'items': 'item_list'}
        
        instance = ListModel()
        instance.items = ['item1', 'item2']
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'items': ['item1', 'item2']})

    def test_to_dict_with_list_of_objects(self):
        """Test to_dict with list of objects - covers lines 34-38"""
        class ListModel(Model):
            types = {'items': list}
            attribute_map = {'items': 'item_list'}
        
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {'serialized': 'object'}
        
        instance = ListModel()
        instance.items = [mock_obj, 'string']
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'items': [{'serialized': 'object'}, 'string']})

    def test_to_dict_with_object(self):
        """Test to_dict with object that has to_dict - covers lines 39-40"""
        class ObjectModel(Model):
            types = {'metadata': dict}
            attribute_map = {'metadata': 'meta_data'}
        
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {'serialized': 'object'}
        
        instance = ObjectModel()
        instance.metadata = mock_obj
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'metadata': {'serialized': 'object'}})

    def test_to_dict_with_dict(self):
        """Test to_dict with dict - covers lines 41-46"""
        class DictModel(Model):
            types = {'metadata': dict}
            attribute_map = {'metadata': 'meta_data'}
        
        instance = DictModel()
        instance.metadata = {'key': 'value'}
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'metadata': {'key': 'value'}})

    def test_to_dict_with_dict_of_objects(self):
        """Test to_dict with dict of objects - covers lines 41-46"""
        class DictModel(Model):
            types = {'metadata': dict}
            attribute_map = {'metadata': 'meta_data'}
        
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {'serialized': 'object'}
        
        instance = DictModel()
        instance.metadata = {'key': mock_obj, 'simple': 'value'}
        
        result = instance.to_dict()
        
        self.assertEqual(result, {'metadata': {'key': {'serialized': 'object'}, 'simple': 'value'}})

    def test_to_str(self):
        """Test to_str method - covers lines 52-57"""
        instance = self.SimpleModel()
        instance.name = 'John'
        
        result = instance.to_str()
        
        self.assertIsInstance(result, str)
        self.assertIn('John', result)

    def test_repr(self):
        """Test __repr__ method - covers lines 59-61"""
        instance = self.SimpleModel()
        instance.name = 'John'
        
        result = repr(instance)
        
        self.assertIsInstance(result, str)
        self.assertIn('John', result)

    def test_eq_same(self):
        """Test __eq__ method with same objects - covers lines 63-65"""
        instance1 = self.SimpleModel()
        instance1.name = 'John'
        
        instance2 = self.SimpleModel()
        instance2.name = 'John'
        
        self.assertTrue(instance1 == instance2)

    def test_eq_different(self):
        """Test __eq__ method with different objects - covers lines 63-65"""
        instance1 = self.SimpleModel()
        instance1.name = 'John'
        
        instance2 = self.SimpleModel()
        instance2.name = 'Jane'
        
        self.assertFalse(instance1 == instance2)

    def test_ne_same(self):
        """Test __ne__ method with same objects - covers lines 67-69"""
        instance1 = self.SimpleModel()
        instance1.name = 'John'
        
        instance2 = self.SimpleModel()
        instance2.name = 'John'
        
        self.assertFalse(instance1 != instance2)

    def test_ne_different(self):
        """Test __ne__ method with different objects - covers lines 67-69"""
        instance1 = self.SimpleModel()
        instance1.name = 'John'
        
        instance2 = self.SimpleModel()
        instance2.name = 'Jane'
        
        self.assertTrue(instance1 != instance2)

    def test_empty_types(self):
        """Test to_dict with empty types - covers lines 32-33"""
        class EmptyModel(Model):
            types = {}
            attribute_map = {}
        
        instance = EmptyModel()
        
        result = instance.to_dict()
        
        self.assertEqual(result, {})


if __name__ == '__main__':
    unittest.main()