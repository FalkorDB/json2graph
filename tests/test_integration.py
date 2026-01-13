"""
Integration tests for JSON Importer with more complex scenarios.
"""

import unittest
import json
import os
import tempfile
from unittest.mock import Mock, patch
from json2graph import JSONImporter


class TestJSONImporterIntegration(unittest.TestCase):
    """Integration test cases for JSONImporter."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_db = Mock()
        self.mock_graph = Mock()
        self.mock_db.select_graph.return_value = self.mock_graph

    @patch('json2graph.json2graph.FalkorDB')
    def test_complex_nested_structure(self, mock_falkordb):
        """Test converting complex nested JSON structure."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "company": "TechCorp",
            "departments": [
                {
                    "name": "Engineering",
                    "employees": [
                        {"name": "Alice", "role": "Engineer"},
                        {"name": "Bob", "role": "Senior Engineer"}
                    ]
                },
                {
                    "name": "Sales",
                    "employees": [
                        {"name": "Charlie", "role": "Sales Rep"}
                    ]
                }
            ],
            "metadata": {
                "founded": 2010,
                "location": {
                    "city": "SF",
                    "country": "USA"
                }
            }
        }

        importer.convert(data, clear_db=True, root_label="Organization")

        # Verify database operations were performed
        self.assertTrue(self.mock_graph.query.called)
        # Should have multiple create operations
        self.assertGreater(self.mock_graph.query.call_count, 5)

    @patch('json2graph.json2graph.FalkorDB')
    def test_cypher_injection_prevention(self, mock_falkordb):
        """Test that malicious input is properly escaped."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        # Try various injection attempts
        data = {
            "malicious1": "'; DROP DATABASE; --",
            "malicious2": "test' OR '1'='1",
            "path": "C:\\Users\\test"
        }

        importer.convert(data)

        # Verify queries were made
        self.assertTrue(self.mock_graph.query.called)

        # Get the CREATE query (first call)
        query = self.mock_graph.query.call_args_list[0][0][0]

        # Verify single quotes are properly escaped (should contain \')
        self.assertIn("\\'", query)

        # Verify the path has escaped backslashes
        self.assertIn("C:\\\\Users\\\\test", query)

        # Verify query structure is valid - should start with CREATE and end properly
        self.assertTrue(query.strip().startswith("CREATE"))
        self.assertTrue(query.strip().endswith("RETURN n"))

    @patch('json2graph.json2graph.FalkorDB')
    def test_array_of_primitives(self, mock_falkordb):
        """Test handling arrays of primitive values."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "tags": ["python", "javascript", "go"],
            "scores": [95, 87, 92, 88],
            "flags": [True, False, True]
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

        # Verify that arrays of scalars are stored as properties
        # Should only have 1 CREATE query for the Root node
        create_queries = [
            call[0][0]
            for call in self.mock_graph.query.call_args_list
            if 'CREATE (n:' in call[0][0]
        ]
        self.assertEqual(len(create_queries), 1, 
                        "Arrays of scalars should not create separate nodes")

        # Verify the CREATE query contains array properties
        create_query = create_queries[0]
        self.assertIn("tags:", create_query)
        self.assertIn("scores:", create_query)
        self.assertIn("flags:", create_query)

    @patch('json2graph.json2graph.FalkorDB')
    def test_scalar_array_as_property(self, mock_falkordb):
        """Test that arrays of scalars are stored as properties, not nodes."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        # This is the exact example from the issue
        data = {
            "name": "John Doe",
            "age": 30,
            "skills": ["Python", "JavaScript"]
        }

        importer.convert(data, clear_db=True)

        # Should have only 2 queries: 1 DELETE + 1 CREATE for the root node
        self.assertEqual(self.mock_graph.query.call_count, 2)

        # Get the CREATE query
        create_queries = [call[0][0] for call in self.mock_graph.query.call_args_list 
                         if 'CREATE' in call[0][0]]
        self.assertEqual(len(create_queries), 1)

        create_query = create_queries[0]

        # Verify it's a single node with array property
        self.assertIn("skills:", create_query)
        # Check that both skill values are present
        self.assertIn("Python", create_query)
        self.assertIn("JavaScript", create_query)
        # Verify the node has the expected Root label
        self.assertIn("CREATE (n:Root", create_query)
        # Should not create Array nodes with "Array" suffix
        self.assertNotIn("Array", create_query.split("CREATE (n:")[1].split()[0])

    @patch('json2graph.json2graph.FalkorDB')
    def test_mixed_array_types(self, mock_falkordb):
        """Test handling arrays with mixed types."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "items": [
                "string",
                123,
                {"object": "value"},
                ["nested", "array"],
                True,
                None
            ]
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_special_characters_in_values(self, mock_falkordb):
        """Test handling special characters in string values."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "text": "It's a test with 'quotes'",
            "description": "Line1\nLine2\nLine3",
            "code": "function() { return 'value'; }"
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_unicode_content(self, mock_falkordb):
        """Test handling Unicode characters."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "name": "José García",
            "greeting": "こんにちは",
            "emoji": "🎉🚀💻"
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_empty_structures(self, mock_falkordb):
        """Test handling empty objects and arrays."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "empty_object": {},
            "empty_array": [],
            "normal_field": "value"
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_numeric_values(self, mock_falkordb):
        """Test handling various numeric types."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = {
            "integer": 42,
            "negative": -10,
            "float": 3.14159,
            "scientific": 1.23e-4,
            "zero": 0
        }

        importer.convert(data)

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_duplicate_content_detection(self, mock_falkordb):
        """Test that duplicate content is detected and prevented."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        # Create same node twice
        data1 = {"name": "Test", "value": 123}
        data2 = {"name": "Test", "value": 123}

        hash1 = importer._generate_hash({"Root": data1})
        hash2 = importer._generate_hash({"Root": data2})

        self.assertEqual(hash1, hash2)

        # Different order should still match
        data3 = {"value": 123, "name": "Test"}
        hash3 = importer._generate_hash({"Root": data3})
        self.assertEqual(hash1, hash3)

    @patch('json2graph.json2graph.FalkorDB')
    def test_clear_db_with_errors(self, mock_falkordb):
        """Test error handling during clear_db operation."""
        mock_falkordb.return_value = self.mock_db
        self.mock_graph.query.side_effect = Exception("Database error")

        importer = JSONImporter()

        with self.assertRaises(Exception) as context:
            importer.clear_db()

        self.assertIn("Failed to clear database", str(context.exception))

    @patch('json2graph.json2graph.FalkorDB')
    def test_load_from_file_with_encoding(self, mock_falkordb):
        """Test loading file with UTF-8 encoding."""
        mock_falkordb.return_value = self.mock_db

        # Create temporary JSON file with Unicode
        test_data = {"name": "José", "message": "Hello 世界"}
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', 
                                        suffix='.json', delete=False) as f:
            json.dump(test_data, f, ensure_ascii=False)
            temp_file = f.name

        try:
            importer = JSONImporter()
            importer.load_from_file(temp_file)

            self.assertTrue(self.mock_graph.query.called)
        finally:
            os.unlink(temp_file)

    @patch('json2graph.json2graph.FalkorDB')
    def test_root_as_array(self, mock_falkordb):
        """Test when root data is an array."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        data = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]

        importer.convert(data, root_label="Items")

        self.assertTrue(self.mock_graph.query.called)

    @patch('json2graph.json2graph.FalkorDB')
    def test_root_as_primitive(self, mock_falkordb):
        """Test when root data is a primitive value."""
        mock_falkordb.return_value = self.mock_db

        importer = JSONImporter()

        # String
        importer.convert("simple string", root_label="Text")
        self.assertTrue(self.mock_graph.query.called)

        self.mock_graph.reset_mock()

        # Number
        importer.convert(42, root_label="Number")
        self.assertTrue(self.mock_graph.query.called)


if __name__ == '__main__':
    unittest.main()
