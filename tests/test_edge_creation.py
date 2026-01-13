"""
Unit test for the edge creation issue fix.
Tests that edges are properly created when converting JSON with nested structures.
"""

import re
import unittest
from unittest.mock import Mock, patch
from json2graph import JSONImporter


class TestEdgeCreation(unittest.TestCase):
    """Test cases for edge creation fix."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock the FalkorDB connection
        self.mock_db = Mock()
        self.mock_graph = Mock()
        self.mock_db.select_graph.return_value = self.mock_graph
        
    @patch('json2graph.json2graph.FalkorDB')
    def test_edges_created_for_nested_objects(self, mock_falkordb):
        """Test that edges are created when JSON contains nested objects in arrays."""
        mock_falkordb.return_value = self.mock_db
        
        # Track all queries
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter(host="localhost", port=6379, graph_name="test_graph")
        
        # This is the exact data from the issue report
        data = {
            "name": "John Doe",
            "age": 30,
            "skills": [{"name": "Python"}, {"name": "JavaScript"}]
        }
        
        importer.convert(data, clear_db=True)
        
        # Extract node creation and relationship queries
        create_queries = [q for q in queries if 'CREATE' in q and 'RETURN n' in q]
        relationship_queries = [q for q in queries if 'MATCH' in q and 'MERGE' in q]
        
        # Should create 4 nodes: Root, skillsArray, Python object, JavaScript object
        self.assertEqual(len(create_queries), 4, 
                         f"Expected 4 nodes to be created, but got {len(create_queries)}")
        
        # Should create 3 relationships:
        # 1. Root -> skillsArray (via "skills" relationship)
        # 2. skillsArray -> Python object (via "ELEMENT_0")
        # 3. skillsArray -> JavaScript object (via "ELEMENT_1")
        self.assertEqual(len(relationship_queries), 3,
                         f"Expected 3 relationships to be created, but got {len(relationship_queries)}")
        
        # Verify that relationship queries reference nodes with matching _hash values
        # Extract all _hash values from CREATE queries
        created_hashes = []
        for query in create_queries:
            hash_match = re.search(r"_hash: '([a-f0-9]+)'", query)
            if hash_match:
                created_hashes.append(hash_match.group(1))
        
        # Check that all relationship queries reference hashes that were created
        for rel_query in relationship_queries:
            hash_matches = re.findall(r"_hash: '([a-f0-9]+)'", rel_query)
            self.assertEqual(len(hash_matches), 2, 
                             f"Relationship query should reference 2 hashes: {rel_query[:100]}")
            
            from_hash, to_hash = hash_matches
            self.assertIn(from_hash, created_hashes,
                          f"Source hash {from_hash} not found in created nodes")
            self.assertIn(to_hash, created_hashes,
                          f"Target hash {to_hash} not found in created nodes")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_hash_property_not_sanitized(self, mock_falkordb):
        """Test that the _hash property key is not sanitized."""
        mock_falkordb.return_value = self.mock_db
        
        # Track all queries
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter()
        
        data = {"name": "test"}
        importer.convert(data, clear_db=True)
        
        # Check that all CREATE queries use _hash (not L_hash or any sanitized version)
        create_queries = [q for q in queries if 'CREATE' in q]
        
        for query in create_queries:
            self.assertIn('_hash:', query, 
                          f"Expected '_hash:' in query, but got: {query}")
            self.assertNotIn('L_hash:', query,
                             f"Found sanitized 'L_hash:' in query: {query}")
    
    @patch('json2graph.json2graph.FalkorDB')
    def test_hash_consistency_in_relationships(self, mock_falkordb):
        """Test that hash values used in relationships match those stored in nodes."""
        mock_falkordb.return_value = self.mock_db
        
        # Track queries
        queries = []
        self.mock_graph.query.side_effect = lambda q: queries.append(q)
        
        importer = JSONImporter()
        
        # Simple nested structure
        data = {
            "parent": "value",
            "child": {"nested": "value"}
        }
        
        importer.convert(data, clear_db=True)
        
        # Extract hashes from node creation
        node_hashes = {}
        for query in queries:
            if 'CREATE' in query:
                label_match = re.search(r'CREATE \(n:(\w+)', query)
                hash_match = re.search(r"_hash: '([a-f0-9]+)'", query)
                if label_match and hash_match:
                    label = label_match.group(1)
                    node_hashes[hash_match.group(1)] = label
        
        # Check all relationship queries use hashes that exist
        relationship_queries = [q for q in queries if 'MATCH' in q and 'MERGE' in q]
        for rel_query in relationship_queries:
            hash_matches = re.findall(r"_hash: '([a-f0-9]+)'", rel_query)
            for hash_val in hash_matches:
                self.assertIn(hash_val, node_hashes,
                              f"Relationship references non-existent hash: {hash_val}")


if __name__ == '__main__':
    unittest.main()
