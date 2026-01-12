"""
Example demonstrating load_from_file functionality with verification.
"""

import json
import sys
import os
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from json_importer import JSONImporter

def verify_file_loading():
    """Verify file loading functionality."""
    print("=" * 60)
    print("json2graph File Loading Demo")
    print("=" * 60)
    
    # Mock the FalkorDB connection
    with patch('json2graph.json2graph.FalkorDB') as mock_falkordb:
        mock_db = Mock()
        mock_graph = Mock()
        mock_db.select_graph.return_value = mock_graph
        mock_falkordb.return_value = mock_db
        
        # Initialize importer
        print("\nInitializing JSONImporter...")
        importer = JSONImporter(host="localhost", port=6379, graph_name="file_demo")
        print("✓ Connected successfully")
        
        # Load from sample file
        sample_file = os.path.join(os.path.dirname(__file__), "sample_data.json")
        
        if os.path.exists(sample_file):
            print(f"\nLoading data from: {sample_file}")
            
            # First, show the contents
            with open(sample_file, 'r') as f:
                data = json.load(f)
            
            print("\nJSON Content Preview:")
            print(json.dumps(data, indent=2)[:500] + "...")
            
            # Load using the importer
            print("\nImporting to graph database...")
            importer.load_from_file(sample_file, clear_db=True)
            
            print(f"✓ File loaded successfully!")
            print(f"✓ Total database operations: {mock_graph.query.call_count}")
            
            # Show what was created
            print("\nExpected Graph Structure:")
            print("  Root Node (Product)")
            print("    ├─ Properties: product, brand, price, in_stock, warranty_years")
            print("    ├─ Relationship: specifications → Object Node")
            print("    │   └─ Properties: processor, ram, storage, graphics, display")
            print("    ├─ Relationship: reviews → Array Node")
            print("    │   └─ Elements: 3 review objects")
            print("    └─ Relationship: tags → Array Node")
            print("        └─ Elements: 4 tag primitives")
            
        else:
            print(f"\n✗ Sample file not found: {sample_file}")
            print("  Creating sample file...")
            
            sample_data = {
                "test": "data",
                "number": 123,
                "nested": {"key": "value"}
            }
            
            with open("test_sample.json", "w") as f:
                json.dump(sample_data, f)
            
            print(f"  Loading from test_sample.json...")
            importer.load_from_file("test_sample.json", clear_db=True)
            print(f"  ✓ Test file loaded successfully!")
            
            # Clean up
            os.remove("test_sample.json")
        
        print("\n" + "=" * 60)
        print("✓ File loading demo completed!")
        print("=" * 60)
        
        # Test error handling
        print("\nTesting Error Handling:")
        
        # Test file not found
        try:
            importer.load_from_file("nonexistent.json")
            print("✗ Should have raised FileNotFoundError")
        except FileNotFoundError as e:
            print(f"✓ FileNotFoundError handled: {str(e)[:50]}...")
        
        # Test invalid JSON
        invalid_file = "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        try:
            importer.load_from_file(invalid_file)
            print("✗ Should have raised ValueError")
        except ValueError as e:
            print(f"✓ ValueError handled: {str(e)[:50]}...")
        finally:
            os.remove(invalid_file)
        
        print("\n" + "=" * 60)

if __name__ == "__main__":
    verify_file_loading()
