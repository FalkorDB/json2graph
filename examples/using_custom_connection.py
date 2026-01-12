"""
Example showing how to use JSONImporter with a pre-initialized FalkorDB connection.
"""

from falkordb import FalkorDB
from json2graph import JSONImporter

def example_with_custom_connection():
    """
    Example of initializing JSONImporter with a custom FalkorDB connection.
    
    This is useful when you want to:
    - Reuse the same connection across multiple components
    - Configure the connection with custom settings (e.g., password, SSL)
    - Manage the connection lifecycle yourself
    """
    print("Example: Using JSONImporter with Custom FalkorDB Connection")
    print("=" * 60)
    
    # Step 1: Create your own FalkorDB connection
    # You have full control over the connection parameters
    db = FalkorDB(host="localhost", port=6379)
    print("\n✓ Created FalkorDB connection")
    
    # Step 2: Pass the connection to JSONImporter
    importer = JSONImporter(db=db, graph_name="custom_example")
    print("✓ Created JSONImporter with custom connection")
    
    # Step 3: Use the importer normally
    data = {
        "company": "TechStartup",
        "founder": "Jane Doe",
        "employees": [
            {"name": "Alice", "role": "Engineer"},
            {"name": "Bob", "role": "Designer"}
        ],
        "funding": {
            "seed_round": 1000000,
            "series_a": 5000000
        }
    }
    
    print("\n✓ Converting JSON data to graph...")
    importer.convert(data, clear_db=True, root_label="Startup")
    print("✓ Data imported successfully!")
    
    # Step 4: You can create another importer with the same connection
    # This reuses the connection to the same database instance
    another_importer = JSONImporter(db=db, graph_name="another_graph")
    print("\n✓ Created another JSONImporter sharing the same connection")
    
    other_data = {
        "product": "Cloud Platform",
        "users": 1500,
        "active": True
    }
    
    another_importer.convert(other_data, clear_db=True, root_label="Product")
    print("✓ Data imported to second graph successfully!")
    
    print("\nBoth importers used the same FalkorDB connection!")


def example_with_connection_pool():
    """
    Example showing connection with custom settings like password.
    
    Note: This example shows the pattern, but won't work without a 
    FalkorDB instance configured with authentication.
    """
    print("\n\nExample: Custom Connection with Authentication")
    print("=" * 60)
    
    try:
        # Create connection with password (requires FalkorDB with auth enabled)
        # db = FalkorDB(host="localhost", port=6379, password="your-password")
        
        # For this example, we'll use a basic connection
        db = FalkorDB(host="localhost", port=6379)
        print("✓ Created FalkorDB connection with custom settings")
        
        importer = JSONImporter(db=db, graph_name="secure_graph")
        print("✓ Created JSONImporter with authenticated connection")
        
        data = {"message": "This connection could be authenticated"}
        importer.convert(data, clear_db=True)
        print("✓ Data imported successfully!")
        
    except Exception as e:
        print(f"Note: This example requires a running FalkorDB instance")
        print(f"Error: {e}")


if __name__ == "__main__":
    print("\nJSONImporter with Custom FalkorDB Connection Examples")
    print("=" * 60)
    print("\nNote: These examples require FalkorDB running on localhost:6379")
    print("\nUncomment the examples you want to run:\n")
    
    # Uncomment to run examples:
    # example_with_custom_connection()
    # example_with_connection_pool()
