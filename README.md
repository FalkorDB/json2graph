
[![license](https://img.shields.io/github/license/falkordb/json2graph.svg)](https://github.com/falkordb/json2graph)
[![Release](https://img.shields.io/github/release/falkordb/json2graph.svg)](https://github.com/falkordb/json2graph/releases/latest)
[![PyPI version](https://badge.fury.io/py/json2graph.svg)](https://badge.fury.io/py/json2graph)
[![Codecov](https://codecov.io/gh/falkordb/json2graph/branch/main/graph/badge.svg)](https://codecov.io/gh/falkordb/json2graph)
[![Forum](https://img.shields.io/badge/Forum-falkordb-blue)](https://github.com/orgs/FalkorDB/discussions)
[![Discord](https://img.shields.io/discord/1146782921294884966?style=flat-square)](https://discord.gg/ErBEqN9E)

# json2graph

[![Try Free](https://img.shields.io/badge/Try%20Free-FalkorDB%20Cloud-FF8101?labelColor=FDE900&style=for-the-badge&link=https://app.falkordb.cloud)](https://app.falkordb.cloud)

A Python library to automatically import JSON to FalkorDB as a Graph.

## Overview

json2graph converts JSON data (from files or dictionaries) into a graph structure in FalkorDB. It automatically creates nodes from objects and arrays with smart labeling based on keys, extracts primitive values as properties, and creates relationships based on the JSON structure. The library handles nested data recursively and prevents duplicate nodes using content hashing.

## Features

- 🔄 **Automatic Graph Creation**: Converts JSON objects and arrays into graph nodes
- 🏷️ **Smart Labeling**: Uses JSON keys to label nodes intelligently
- 🔗 **Relationship Mapping**: Creates relationships based on JSON structure
- 📦 **Property Extraction**: Extracts primitive values (strings, numbers, booleans) as node properties
- 🔁 **Recursive Processing**: Handles deeply nested JSON structures
- 🔒 **Duplicate Prevention**: Uses content hashing to prevent duplicate nodes
- 🗂️ **File & Dict Support**: Import from JSON files or Python dictionaries
- 🧹 **Database Management**: Optional database clearing before import
- 🔌 **FalkorDB Integration**: Uses FalkorDB Python client with Cypher queries via GRAPH.QUERY

## Installation

### Using uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package installer and resolver, written in Rust. It's recommended for faster dependency resolution and installation.

Install uv if you haven't already:
```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or via pip
pip install uv
```

Then install json2graph for development (editable mode):
```bash
uv pip install -e .
```

Or install dependencies directly:
```bash
uv pip install falkordb
```

### Using pip

For development (editable mode):
```bash
pip install -e .
```

Or install dependencies directly:

```bash
pip install falkordb
```

## Quick Start

```python
from json2graph import JSONImporter

# Initialize the importer
importer = JSONImporter(
    host="localhost",
    port=6379,
    graph_name="my_graph"
)

# Import from a dictionary
data = {
    "name": "John Doe",
    "age": 30,
    "skills": ["Python", "JavaScript"]
}
importer.convert(data, clear_db=True)

# Import from a JSON file
importer.load_from_file("data.json", clear_db=True)
```

## Usage

### Initialize the Importer

```python
from json2graph import JSONImporter

importer = JSONImporter(
    host="localhost",      # FalkorDB host (default: "localhost")
    port=6379,            # FalkorDB port (default: 6379)
    graph_name="my_graph" # Graph database name (default: "json_graph")
)
```

### Convert JSON Dictionary

```python
# Simple object
data = {
    "product": "Laptop",
    "price": 999.99,
    "in_stock": True
}
importer.convert(data, clear_db=True, root_label="Product")
```

### Load from JSON File

```python
# Load and convert JSON file
importer.load_from_file("data.json", clear_db=True)
```

### Nested Structures

The library handles nested objects and arrays automatically:

```python
data = {
    "company": "TechCorp",
    "employees": [
        {
            "name": "Alice",
            "role": "Developer",
            "skills": ["Python", "Go"]
        },
        {
            "name": "Bob",
            "role": "Designer",
            "skills": ["Photoshop"]
        }
    ],
    "location": {
        "city": "San Francisco",
        "country": "USA"
    }
}
importer.convert(data, root_label="Company")
```

### Clear Database

```python
# Clear all nodes and relationships
importer.clear_db()

# Or clear during import
importer.convert(data, clear_db=True)
importer.load_from_file("data.json", clear_db=True)
```

## How It Works

1. **Node Creation**: 
   - JSON objects become nodes with labels derived from their keys
   - JSON arrays become container nodes with element relationships
   - Primitive values become node properties

2. **Smart Labeling**:
   - Object nodes are labeled based on their parent key
   - Array nodes get "Array" suffix (e.g., "employeesArray")
   - Labels are sanitized for Cypher compatibility

3. **Relationships**:
   - Parent-child relationships are created based on JSON structure
   - Relationship types are derived from JSON keys
   - Array elements get indexed relationships (e.g., "ELEMENT_0", "ELEMENT_1")

4. **Duplicate Prevention**:
   - Content hashing (SHA256) identifies duplicate nodes
   - Identical content creates only one node in the graph
   - Cache prevents redundant database queries

5. **Cypher Execution**:
   - All operations use FalkorDB's GRAPH.QUERY command
   - Cypher queries are generated automatically
   - Transactions ensure data consistency

## API Reference

### JSONImporter

#### `__init__(host="localhost", port=6379, graph_name="json_graph")`

Initialize the JSON Importer.

**Parameters:**
- `host` (str): FalkorDB host address
- `port` (int): FalkorDB port number
- `graph_name` (str): Name of the graph database

#### `convert(data, clear_db=False, root_label="Root")`

Convert JSON data into a graph structure.

**Parameters:**
- `data` (Union[Dict, List, Any]): JSON data as dict, list, or primitive value
- `clear_db` (bool): If True, clear the database before importing
- `root_label` (str): Label for the root node

#### `load_from_file(filepath, clear_db=False)`

Load JSON data from a file and import it into the graph.

**Parameters:**
- `filepath` (str): Path to the JSON file
- `clear_db` (bool): If True, clear the database before importing

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `ValueError`: If the file contains invalid JSON

#### `clear_db()`

Clear all data from the current graph database.

## Examples

See the `examples/` directory for more detailed examples:

- `basic_usage.py`: Simple usage examples with various JSON structures

## Testing

Run the test suite using unittest:

```bash
python -m unittest discover tests
```

With verbose output:

```bash
python -m unittest discover tests -v
```

Or using pytest (if installed):

```bash
# Install pytest with uv
uv pip install pytest

# Run tests
python -m pytest tests/
```

## Requirements

- Python >= 3.8
- falkordb >= 1.0.0
- FalkorDB server running and accessible

## License

MIT License - see LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues and questions, please open an issue on the GitHub repository.
