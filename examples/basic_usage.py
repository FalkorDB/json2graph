"""
Example usage of the JSON Importer library.
"""

from json_importer import JSONImporter

# Example 1: Simple JSON object
def example_simple_object():
    """Import a simple JSON object."""
    importer = JSONImporter(host="localhost", port=6379, graph_name="example_graph")
    
    data = {
        "name": "John Doe",
        "age": 30,
        "email": "john@example.com"
    }
    
    importer.convert(data, clear_db=True, root_label="Person")
    print("Simple object imported successfully!")

# Example 2: Nested JSON structure
def example_nested_structure():
    """Import nested JSON structure."""
    importer = JSONImporter(host="localhost", port=6379, graph_name="example_graph")
    
    data = {
        "company": "TechCorp",
        "employees": [
            {
                "name": "Alice",
                "position": "Developer",
                "skills": ["Python", "JavaScript", "SQL"]
            },
            {
                "name": "Bob",
                "position": "Designer",
                "skills": ["Photoshop", "Illustrator"]
            }
        ],
        "location": {
            "city": "San Francisco",
            "country": "USA"
        }
    }
    
    importer.convert(data, clear_db=True, root_label="Company")
    print("Nested structure imported successfully!")

# Example 3: Load from file
def example_from_file():
    """Import JSON from a file."""
    import json
    
    # Create a sample JSON file
    sample_data = {
        "product": "Laptop",
        "price": 999.99,
        "specs": {
            "cpu": "Intel i7",
            "ram": "16GB",
            "storage": "512GB SSD"
        },
        "reviews": [
            {"author": "User1", "rating": 5, "comment": "Great laptop!"},
            {"author": "User2", "rating": 4, "comment": "Good value"}
        ]
    }
    
    # Save to file
    with open("sample_product.json", "w") as f:
        json.dump(sample_data, f)
    
    # Import from file
    importer = JSONImporter(host="localhost", port=6379, graph_name="example_graph")
    importer.load_from_file("sample_product.json", clear_db=True)
    print("Data imported from file successfully!")

# Example 4: Array of objects
def example_array_of_objects():
    """Import an array of objects."""
    importer = JSONImporter(host="localhost", port=6379, graph_name="example_graph")
    
    data = [
        {"id": 1, "title": "Post 1", "author": "Alice"},
        {"id": 2, "title": "Post 2", "author": "Bob"},
        {"id": 3, "title": "Post 3", "author": "Alice"}
    ]
    
    importer.convert(data, clear_db=True, root_label="Posts")
    print("Array of objects imported successfully!")

if __name__ == "__main__":
    print("JSON Importer Examples")
    print("=" * 50)
    print("\nNote: Make sure FalkorDB is running on localhost:6379")
    print("\nUncomment the examples you want to run:\n")
    
    # Uncomment to run examples:
    # example_simple_object()
    # example_nested_structure()
    # example_from_file()
    # example_array_of_objects()
