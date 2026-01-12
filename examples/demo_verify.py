"""
Demo script to verify JSON Importer functionality without database.
This script tests the core functionality without requiring a running FalkorDB instance.
"""

import json
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_importer import JSONImporter

def demo_without_db():
    """Demonstrate JSON Importer functionality with mocked database."""
    print("=" * 60)
    print("JSON-importer Demo (Mocked Database)")
    print("=" * 60)
    
    # Mock the FalkorDB connection
    with patch('json_importer.json_importer.FalkorDB') as mock_falkordb:
        mock_db = Mock()
        mock_graph = Mock()
        mock_db.select_graph.return_value = mock_graph
        mock_falkordb.return_value = mock_db
        
        # Initialize importer
        print("\n1. Initializing JSONImporter...")
        importer = JSONImporter(host="localhost", port=6379, graph_name="demo_graph")
        print("   ✓ Connected to graph 'demo_graph'")
        
        # Test simple object
        print("\n2. Converting simple JSON object...")
        simple_data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "active": True
        }
        print(f"   Data: {json.dumps(simple_data, indent=2)}")
        importer.convert(simple_data, root_label="Person")
        print(f"   ✓ Created {mock_graph.query.call_count} database operations")
        
        # Reset mock
        mock_graph.reset_mock()
        
        # Test nested structure
        print("\n3. Converting nested JSON structure...")
        nested_data = {
            "company": "TechCorp",
            "founded": 2010,
            "employees": [
                {
                    "name": "Alice",
                    "position": "Developer",
                    "skills": ["Python", "JavaScript"]
                },
                {
                    "name": "Bob",
                    "position": "Designer"
                }
            ],
            "location": {
                "city": "San Francisco",
                "country": "USA"
            }
        }
        print(f"   Data: {json.dumps(nested_data, indent=2)}")
        importer.convert(nested_data, root_label="Company")
        print(f"   ✓ Created {mock_graph.query.call_count} database operations")
        
        # Test hash generation
        print("\n4. Testing duplicate prevention...")
        hash1 = importer._generate_hash({"name": "test", "value": 123})
        hash2 = importer._generate_hash({"name": "test", "value": 123})
        hash3 = importer._generate_hash({"name": "test", "value": 456})
        print(f"   Hash 1: {hash1[:16]}...")
        print(f"   Hash 2: {hash2[:16]}... (same content)")
        print(f"   Hash 3: {hash3[:16]}... (different content)")
        print(f"   ✓ Hash 1 == Hash 2: {hash1 == hash2}")
        print(f"   ✓ Hash 1 != Hash 3: {hash1 != hash3}")
        
        # Test label sanitization
        print("\n5. Testing label sanitization...")
        test_labels = [
            "valid_label",
            "label-with-dash",
            "label with spaces",
            "123numeric",
            "special!@#$chars"
        ]
        for label in test_labels:
            sanitized = importer._sanitize_label(label)
            print(f"   '{label}' -> '{sanitized}'")
        
        # Test property formatting
        print("\n6. Testing property formatting...")
        props = {
            "string": "hello",
            "number": 42,
            "float": 3.14,
            "boolean": True,
            "none": None
        }
        formatted = importer._format_properties(props)
        print(f"   Properties: {props}")
        print(f"   Formatted: {formatted}")
        
        print("\n" + "=" * 60)
        print("✓ All demos completed successfully!")
        print("=" * 60)
        print("\nKey Features Demonstrated:")
        print("  ✓ Database connection handling")
        print("  ✓ Simple object conversion")
        print("  ✓ Nested structure handling")
        print("  ✓ Array processing")
        print("  ✓ Duplicate prevention with hashing")
        print("  ✓ Label sanitization for Cypher")
        print("  ✓ Property formatting for queries")
        print("\nTo use with a real FalkorDB instance:")
        print("  1. Start FalkorDB server (default: localhost:6379)")
        print("  2. Run: python examples/basic_usage.py")

if __name__ == "__main__":
    demo_without_db()
