"""
Unit tests for JSON Importer.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, MagicMock, patch
from json2graph import JSONImporter


class TestJSONImporter(unittest.TestCase):
    """Test cases for JSONImporter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the FalkorDB connection
        self.mock_db = Mock()
        self.mock_graph = Mock()
        self.mock_db.select_graph.return_value = self.mock_graph
        
    @patch('json2graph.json2graph.FalkorDB')
    def test_init(self, mock_falkordb):
        """Test JSONImporter initialization."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter(host="testhost", port=1234, graph_name="testgraph")
        
        self.assertEqual(importer.host, "testhost")
        self.assertEqual(importer.port, 1234)
        self.assertEqual(importer.graph_name, "testgraph")
        mock_falkordb.assert_called_once_with(host="testhost", port=1234)
        
    @patch('json2graph.json2graph.FalkorDB')
    def test_clear_db(self, mock_falkordb):
        """Test clearing the database."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        importer.clear_db()
        
        self.mock_graph.query.assert_called_once_with("MATCH (n) DETACH DELETE n")
        self.assertEqual(len(importer._node_cache), 0)
        
    @patch('json2graph.json2graph.FalkorDB')
    def test_load_from_file(self, mock_falkordb):
        """Test loading JSON from file."""
        mock_falkordb.return_value = self.mock_db
        
        # Create temporary JSON file
        test_data = {"name": "test", "value": 123}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(test_data, f)
            temp_file = f.name
        
        try:
            importer = JSONImporter()
            importer.load_from_file(temp_file)
            
            # Verify that graph queries were made
            self.assertTrue(self.mock_graph.query.called)
        finally:
            os.unlink(temp_file)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_load_from_file_not_found(self, mock_falkordb):
        """Test loading from non-existent file."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        with self.assertRaises(FileNotFoundError):
            importer.load_from_file("nonexistent.json")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_load_from_file_invalid_json(self, mock_falkordb):
        """Test loading invalid JSON from file."""
        mock_falkordb.return_value = self.mock_db
        
        # Create temporary file with invalid JSON
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_file = f.name
        
        try:
            importer = JSONImporter()
            
            with self.assertRaises(ValueError):
                importer.load_from_file(temp_file)
        finally:
            os.unlink(temp_file)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_convert_simple_dict(self, mock_falkordb):
        """Test converting a simple dictionary."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        data = {"name": "John", "age": 30}
        
        importer.convert(data)
        
        # Verify that graph queries were made
        self.assertTrue(self.mock_graph.query.called)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_convert_with_clear_db(self, mock_falkordb):
        """Test converting with clear_db option."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        data = {"test": "data"}
        
        importer.convert(data, clear_db=True)
        
        # Verify clear was called
        calls = [str(call) for call in self.mock_graph.query.call_args_list]
        self.assertTrue(any("DETACH DELETE" in call for call in calls))
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_sanitize_label(self, mock_falkordb):
        """Test label sanitization."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        self.assertEqual(importer._sanitize_label("valid_label"), "valid_label")
        self.assertEqual(importer._sanitize_label("label-with-dash"), "label_with_dash")
        self.assertEqual(importer._sanitize_label("label with spaces"), "label_with_spaces")
        self.assertEqual(importer._sanitize_label("123label"), "L123label")
        self.assertEqual(importer._sanitize_label(""), "Node")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_generate_hash(self, mock_falkordb):
        """Test hash generation for duplicate detection."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Same content should generate same hash
        hash1 = importer._generate_hash({"a": 1, "b": 2})
        hash2 = importer._generate_hash({"a": 1, "b": 2})
        self.assertEqual(hash1, hash2)
        
        # Different content should generate different hash
        hash3 = importer._generate_hash({"a": 1, "b": 3})
        self.assertNotEqual(hash1, hash3)
        
        # Order shouldn't matter for dicts
        hash4 = importer._generate_hash({"b": 2, "a": 1})
        self.assertEqual(hash1, hash4)
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_format_properties(self, mock_falkordb):
        """Test property formatting for Cypher queries."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Test string property
        props = {"name": "John"}
        formatted = importer._format_properties(props)
        self.assertIn("name: 'John'", formatted)
        
        # Test number property
        props = {"age": 30}
        formatted = importer._format_properties(props)
        self.assertIn("age: 30", formatted)
        
        # Test boolean property
        props = {"active": True}
        formatted = importer._format_properties(props)
        self.assertIn("active: true", formatted)
        
        # Test null property
        props = {"value": None}
        formatted = importer._format_properties(props)
        self.assertIn("value: null", formatted)
        
        # Test empty dict
        props = {}
        formatted = importer._format_properties(props)
        self.assertEqual(formatted, "{}")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_escape_string(self, mock_falkordb):
        """Test string escaping for Cypher injection prevention."""
        mock_falkordb.return_value = self.mock_db
        
        importer = JSONImporter()
        
        # Test backslash escaping
        escaped = importer._escape_string("path\\to\\file")
        self.assertEqual(escaped, "path\\\\to\\\\file")
        
        # Test single quote escaping
        escaped = importer._escape_string("It's a test")
        self.assertEqual(escaped, "It\\'s a test")
        
        # Test both backslash and quote
        escaped = importer._escape_string("C:\\user's\\path")
        self.assertEqual(escaped, "C:\\\\user\\'s\\\\path")
        
        # Test normal string (no special chars)
        escaped = importer._escape_string("normal text")
        self.assertEqual(escaped, "normal text")


if __name__ == '__main__':
    unittest.main()
