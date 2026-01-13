"""
Additional tests to improve code coverage for edge cases and error paths.
"""

import re
import json
import tempfile
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from json2graph import JSONImporter


class TestCoverageGaps(unittest.TestCase):
    """Test cases to cover edge cases and error paths."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_graph = Mock()
        self.mock_db.select_graph.return_value = self.mock_graph
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_load_from_file_with_clear_db(self, mock_falkordb):
        """Test load_from_file with clear_db=True."""
        mock_falkordb.return_value = self.mock_db
        
        # Create temporary JSON file
        test_data = {"name": "test", "value": 123}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            importer = JSONImporter()
            # Call with clear_db=True to hit that path
            importer.load_from_file(temp_file, clear_db=True)
            
            # Verify that clear_db was called (DETACH DELETE query)
            calls = [call[0][0] for call in self.mock_graph.query.call_args_list]
            self.assertTrue(any("DETACH DELETE" in call for call in calls),
                           f"Expected DETACH DELETE in queries: {calls}")
        finally:
            os.unlink(temp_file)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_create_node_with_existing_hash(self, mock_falkordb):
        """Test _create_node when hash is already in properties."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Pre-generate a hash
        test_hash = importer._generate_hash({"test": "data"})
        properties = {"value": "test", "_hash": test_hash}
        
        node_id = importer._create_node("TestLabel", properties)
        
        # Should return the provided hash
        self.assertEqual(node_id, test_hash)
        # Should have called graph.query
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_create_node_caching(self, mock_falkordb):
        """Test that _create_node uses cache for duplicate hashes."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Create same node twice
        properties1 = {"value": "test", "_hash": "somehash123"}
        importer._node_cache["somehash123"] = True
        
        properties2 = {"value": "test", "_hash": "somehash123"}
        
        # Call with cached hash
        node_id = importer._create_node("TestLabel", properties2)
        
        # Should return hash without creating a node
        self.assertEqual(node_id, "somehash123")
        # Query should not be called since it's cached
        self.mock_graph.query.assert_not_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_create_node_with_exception(self, mock_falkordb):
        """Test exception handling in _create_node."""
        mock_falkordb.return_value = self.mock_db
        self.mock_graph.query.side_effect = Exception("Database error")
        
        importer = JSONImporter()
        
        # Clear cache to ensure the query is actually called
        importer._node_cache.clear()
        properties = {"value": "test"}
        
        with self.assertRaises(Exception) as context:
            importer._create_node("TestLabel", properties)
        
        self.assertIn("Failed to create node", str(context.exception))
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_create_relationship_with_exception(self, mock_falkordb):
        """Test exception handling in _create_relationship."""
        mock_falkordb.return_value = self.mock_db
        self.mock_graph.query.side_effect = Exception("Node not found")
        
        importer = JSONImporter()
        
        # Should log warning but not raise
        importer._create_relationship("from_id", "to_id", "TEST_REL")
        
        # Query should have been attempted
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_value_with_none_no_parent(self, mock_falkordb):
        """Test _process_value handles None at root level."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Process None value without parent (root level)
        result = importer._process_value(
            value=None,
            parent_node_id=None,
            relationship_name="test",
            key_name="nullValue"
        )
        
        # Should create a Null node
        self.assertIsNotNone(result)
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_value_with_none_with_parent(self, mock_falkordb):
        """Test _process_value skips None when there's a parent."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Process None value with parent
        result = importer._process_value(
            value=None,
            parent_node_id="parent_hash",
            relationship_name="test",
            key_name="nullValue"
        )
        
        # Should return None and not create a node
        self.assertIsNone(result)
        self.mock_graph.query.assert_not_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_primitive_with_parent(self, mock_falkordb):
        """Test _process_value with primitive value and parent."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Process primitive with parent - should return None
        result = importer._process_value(
            value="primitive_string",
            parent_node_id="parent_hash",
            relationship_name="test",
            key_name="stringField"
        )
        
        # Should return None (primitives with parent don't create nodes)
        self.assertIsNone(result)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_primitive_without_parent(self, mock_falkordb):
        """Test _process_value with primitive value at root."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Process primitive at root
        result = importer._process_value(
            value=42,
            parent_node_id=None,
            relationship_name="Root",
            key_name="IntValue"
        )
        
        # Should create a node
        self.assertIsNotNone(result)
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_primitive_without_key_name(self, mock_falkordb):
        """Test _process_value with primitive value and no key_name."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Capture the query calls
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        # Process primitive at root without key_name
        result = importer._process_value(
            value="test",
            parent_node_id=None,
            relationship_name="Root",
            key_name=""  # Empty key_name
        )
        
        # Should create a node with "Primitive" label
        self.assertIsNotNone(result)
        # Check that Primitive label was used (key_name or "Primitive")
        self.assertTrue(any(":Primitive" in q for q in queries),
                       f"Expected ':Primitive' label in queries: {queries}")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_object_without_parent(self, mock_falkordb):
        """Test _process_object creates node without parent."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        obj = {"name": "test", "value": 123}
        result = importer._process_object(
            obj=obj,
            parent_node_id=None,
            relationship_name="Root",
            key_name="TestObj"
        )
        
        # Should create a node
        self.assertIsNotNone(result)
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_object_with_parent(self, mock_falkordb):
        """Test _process_object creates relationship to parent."""
        mock_falkordb.return_value = self.mock_db
        
        # Track queries to verify both CREATE and MERGE
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter()
        
        obj = {"name": "test"}
        result = importer._process_object(
            obj=obj,
            parent_node_id="parent_hash_123",
            relationship_name="child",
            key_name="Child"
        )
        
        # Should create node and relationship
        self.assertIsNotNone(result)
        # Should have CREATE query
        create_queries = [q for q in queries if "CREATE" in q]
        self.assertGreater(len(create_queries), 0)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_object_without_key_name(self, mock_falkordb):
        """Test _process_object without key_name."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        obj = {"value": "test"}
        result = importer._process_object(
            obj=obj,
            parent_node_id=None,
            relationship_name="Root",
            key_name=""  # Empty key_name
        )
        
        # Should use "Object" as label
        self.assertIsNotNone(result)
        calls = self.mock_graph.query.call_args_list
        self.assertTrue(any("Object" in str(call) for call in calls))
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_object_with_nested_values(self, mock_falkordb):
        """Test _process_object with nested objects and arrays."""
        mock_falkordb.return_value = self.mock_db
        
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter()
        
        obj = {
            "scalar": "value",
            "scalar_array": [1, 2, 3],
            "nested": {"inner": "value"},
            "nested_array": [{"id": 1}]
        }
        
        result = importer._process_object(obj, None, "Root", "TestObj")
        
        self.assertIsNotNone(result)
        # Should have multiple queries for nested structures
        self.assertGreater(len(queries), 1)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_array_without_parent(self, mock_falkordb):
        """Test _process_array without parent."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        arr = [1, 2, 3]
        result = importer._process_array(arr, None, "Root", "Numbers")
        
        self.assertIsNotNone(result)
        self.mock_graph.query.assert_called()
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_array_with_parent(self, mock_falkordb):
        """Test _process_array with parent."""
        mock_falkordb.return_value = self.mock_db
        
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter()
        
        arr = ["a", "b", "c"]
        result = importer._process_array(
            arr,
            parent_node_id="parent_hash",
            relationship_name="items",
            key_name="StringArray"
        )
        
        # Should create array node and relationship
        self.assertIsNotNone(result)
        # Should have both CREATE and MERGE queries
        merge_queries = [q for q in queries if "MERGE" in q]
        self.assertGreater(len(merge_queries), 0)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_array_with_complex_items(self, mock_falkordb):
        """Test _process_array with complex items."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        arr = [
            {"id": 1, "data": "first"},
            {"id": 2, "data": "second"},
            [1, 2, 3]
        ]
        
        result = importer._process_array(arr, None, "Root", "Mixed")
        
        self.assertIsNotNone(result)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_process_array_without_key_name(self, mock_falkordb):
        """Test _process_array without key_name."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        arr = [1, 2, 3]
        result = importer._process_array(arr, None, "Root", "")
        
        # Should use "Array" as label
        self.assertIsNotNone(result)
        calls = self.mock_graph.query.call_args_list
        self.assertTrue(any("Array" in str(call) for call in calls))
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_value_string(self, mock_falkordb):
        """Test _format_value with string."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._format_value("test string")
        self.assertEqual(result, "'test string'")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_value_boolean(self, mock_falkordb):
        """Test _format_value with boolean."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        self.assertEqual(importer._format_value(True), "true")
        self.assertEqual(importer._format_value(False), "false")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_value_numbers(self, mock_falkordb):
        """Test _format_value with numbers."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        self.assertEqual(importer._format_value(42), "42")
        self.assertEqual(importer._format_value(3.14), "3.14")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_value_null(self, mock_falkordb):
        """Test _format_value with null."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        self.assertEqual(importer._format_value(None), "null")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_value_complex_object(self, mock_falkordb):
        """Test _format_value with complex object."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Should convert to string and quote
        result = importer._format_value({"nested": "object"})
        self.assertTrue(result.startswith("'"))
        self.assertTrue(result.endswith("'"))
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_properties_empty(self, mock_falkordb):
        """Test _format_properties with empty dict."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._format_properties({})
        self.assertEqual(result, "{}")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_properties_with_array(self, mock_falkordb):
        """Test _format_properties with array property."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        properties = {
            "tags": ["python", "javascript"],
            "scores": [95, 87]
        }
        
        result = importer._format_properties(properties)
        
        # Should contain array syntax
        self.assertIn("[", result)
        self.assertIn("]", result)
        self.assertIn("tags:", result)
        self.assertIn("scores:", result)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_properties_mixed_types(self, mock_falkordb):
        """Test _format_properties with mixed value types."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        properties = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "null": None,
            "array": [1, 2]
        }
        
        result = importer._format_properties(properties)
        
        # Verify structure
        self.assertIn("{", result)
        self.assertIn("}", result)
        self.assertIn("true", result)
        self.assertIn("null", result)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_sanitize_label_empty_string(self, mock_falkordb):
        """Test _sanitize_label with empty string."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._sanitize_label("")
        self.assertEqual(result, "Node")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_sanitize_label_special_chars(self, mock_falkordb):
        """Test _sanitize_label with various special characters."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Test various special chars
        self.assertEqual(importer._sanitize_label("test-label"), "test_label")
        self.assertEqual(importer._sanitize_label("test.label"), "test_label")
        self.assertEqual(importer._sanitize_label("test label"), "test_label")
        self.assertEqual(importer._sanitize_label("test@#$%label"), "test____label")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_sanitize_label_starts_with_number(self, mock_falkordb):
        """Test _sanitize_label when it starts with a number."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._sanitize_label("123label")
        self.assertTrue(result.startswith("L"))
        self.assertIn("123label", result)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_escape_string_with_quotes(self, mock_falkordb):
        """Test _escape_string with single quotes."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._escape_string("It's a test")
        self.assertEqual(result, "It\\'s a test")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_escape_string_with_backslashes(self, mock_falkordb):
        """Test _escape_string with backslashes."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._escape_string("C:\\Users\\test")
        self.assertEqual(result, "C:\\\\Users\\\\test")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_escape_string_with_both(self, mock_falkordb):
        """Test _escape_string with both quotes and backslashes."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        result = importer._escape_string("C:\\user's\\path")
        self.assertEqual(result, "C:\\\\user\\'s\\\\path")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_generate_hash_consistency(self, mock_falkordb):
        """Test that _generate_hash produces consistent results."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        data = {"key": "value", "nested": {"inner": "data"}}
        
        hash1 = importer._generate_hash(data)
        hash2 = importer._generate_hash(data)
        
        self.assertEqual(hash1, hash2)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_generate_hash_with_list(self, mock_falkordb):
        """Test _generate_hash with list."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        data = [1, 2, 3, {"key": "value"}]
        
        hash_val = importer._generate_hash(data)
        self.assertTrue(isinstance(hash_val, str))
        self.assertEqual(len(hash_val), 64)  # SHA256 hex is 64 chars
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_generate_hash_with_primitives(self, mock_falkordb):
        """Test _generate_hash with primitive types (not dict/list)."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Test with string
        hash1 = importer._generate_hash("simple string")
        self.assertEqual(len(hash1), 64)
        
        # Test with number
        hash2 = importer._generate_hash(42)
        self.assertEqual(len(hash2), 64)
        
        # Test with boolean
        hash3 = importer._generate_hash(True)
        self.assertEqual(len(hash3), 64)
        
        # Test with None
        hash4 = importer._generate_hash(None)
        self.assertEqual(len(hash4), 64)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_is_scalar_array_with_non_list(self, mock_falkordb):
        """Test _is_scalar_array with non-list input."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Should return False for non-list inputs
        self.assertFalse(importer._is_scalar_array("string"))
        self.assertFalse(importer._is_scalar_array(42))
        self.assertFalse(importer._is_scalar_array({"dict": "value"}))
        self.assertFalse(importer._is_scalar_array(None))


if __name__ == '__main__':
    unittest.main()
