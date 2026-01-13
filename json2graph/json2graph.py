"""
Main module for JSON to FalkorDB graph converter.
"""

import json
import hashlib
import logging
from typing import Any, Dict, List, Optional, Union
from falkordb import FalkorDB

# Set up module logger
logger = logging.getLogger(__name__)


class JSONImporter:
    """
    Converts JSON data into FalkorDB graph database.

    Reads JSON files/dicts, automatically creates nodes from objects/arrays with
    smart labeling from keys, extracts primitives as properties, creates relationships
    based on structure. Handles nested data recursively and prevents duplicates with
    content hashing.
    """

    def __init__(
        self,
        db: Optional[FalkorDB] = None,
        host: str = "localhost",
        port: int = 6379,
        graph_name: str = "json_graph",
    ):
        """
        Initialize the JSON Importer with database connection details.

        Args:
            db: Pre-initialized FalkorDB connection (optional).
                If provided, host and port are ignored.
            host: FalkorDB host address (used only if db is not provided)
            port: FalkorDB port number (used only if db is not provided)
            graph_name: Name of the graph database
        """
        self.graph_name = graph_name

        if db is not None:
            # Use the provided FalkorDB connection
            self.db = db
            self.host = None
            self.port = None
        else:
            # Create a new connection with provided host and port
            self.host = host
            self.port = port
            self.db = FalkorDB(host=host, port=port)

        self.graph = self.db.select_graph(graph_name)
        self._node_cache = {}  # Cache for content hash to node mapping

    def clear_db(self):
        """Clear all data from the current graph database."""
        try:
            self.graph.query("MATCH (n) DETACH DELETE n")
            self._node_cache.clear()
        except Exception as e:
            raise Exception(f"Failed to clear database: {str(e)}") from e

    def load_from_file(self, filepath: str, clear_db: bool = False) -> None:
        """
        Load JSON data from a file and import it into the graph database.

        Args:
            filepath: Path to the JSON file
            clear_db: If True, clear the database before importing
        """
        if clear_db:
            self.clear_db()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.convert(data, clear_db=False)  # Already cleared if needed
        except FileNotFoundError as exc:
            raise FileNotFoundError(f"File not found: {filepath}") from exc
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in file {filepath}: {str(e)}") from e

    def convert(
        self,
        data: Union[Dict, List, Any],
        clear_db: bool = False,
        root_label: str = "Root",
    ) -> None:
        """
        Convert JSON data into a graph structure in FalkorDB.

        Args:
            data: JSON data as dict, list, or primitive value
            clear_db: If True, clear the database before importing
            root_label: Label for the root node
        """
        if clear_db:
            self.clear_db()

        # Process the root data
        self._process_value(
            data,
            parent_node_id=None,
            relationship_name=root_label,
            key_name=root_label,
        )

    def _generate_hash(self, content: Any) -> str:
        """
        Generate a hash for content to identify duplicate nodes.

        Args:
            content: The content to hash

        Returns:
            SHA256 hash of the content
        """
        # Convert content to a stable string representation
        if isinstance(content, (dict, list)):
            content_str = json.dumps(content, sort_keys=True, default=str)
        else:
            content_str = str(content)

        return hashlib.sha256(content_str.encode()).hexdigest()

    def _create_node(self, label: str, properties: Dict[str, Any]) -> str:
        """
        Create a node in the graph database.

        Args:
            label: Node label
            properties: Node properties (may include _hash)

        Returns:
            Node ID (hash)
        """
        # Use the provided _hash if it exists, otherwise generate one
        # This ensures the hash we return matches what's stored in the node
        # Note: When generating a new hash, we calculate it BEFORE adding _hash to properties
        # to avoid including _hash in its own hash calculation (circular reference)
        if "_hash" in properties:
            node_hash = properties["_hash"]
        else:
            # Generate hash for duplicate detection based on label and current properties
            node_hash = self._generate_hash({label: properties})
            # Add the hash to properties so it's stored in the node for relationship matching
            properties["_hash"] = node_hash

        # Check if node already exists in cache
        if node_hash in self._node_cache:
            return node_hash

        # Escape property values for Cypher query
        props_str = self._format_properties(properties)

        # Create node using Cypher query
        query = f"CREATE (n:{self._sanitize_label(label)} {props_str}) RETURN n"
        try:
            self.graph.query(query)
            self._node_cache[node_hash] = True
        except Exception as e:
            raise Exception(f"Failed to create node: {str(e)}") from e

        return node_hash

    def _create_relationship(self, from_id: str, to_id: str, rel_type: str) -> None:
        """
        Create a relationship between two nodes.

        Args:
            from_id: Source node hash
            to_id: Target node hash
            rel_type: Relationship type
        """
        # Create relationship using node content hashes
        rel_type_sanitized = self._sanitize_label(rel_type)

        # Escape hash values to prevent injection
        from_id_escaped = self._escape_string(from_id)
        to_id_escaped = self._escape_string(to_id)

        # Use a more efficient query pattern that filters nodes directly
        # instead of creating a cartesian product
        query = f"""
        MATCH (a {{_hash: '{from_id_escaped}'}}), (b {{_hash: '{to_id_escaped}'}})
        MERGE (a)-[r:{rel_type_sanitized}]->(b)
        """
        try:
            self.graph.query(query)
        except Exception as e:
            # Log the error but continue processing
            # Relationships might fail if nodes don't have _hash property initially
            # or if nodes haven't been created yet
            logger.warning(
                "Failed to create relationship %s from %s... to %s...: %s",
                rel_type_sanitized,
                from_id[:8],
                to_id[:8],
                str(e),
            )

    def _process_value(
        self,
        value: Any,
        parent_node_id: Optional[str],
        relationship_name: str,
        key_name: str,
    ) -> Optional[str]:
        """
        Process a JSON value recursively and create appropriate graph structures.

        Args:
            value: The value to process
            parent_node_id: Parent node hash (if any)
            relationship_name: Name for the relationship from parent
            key_name: Key name for labeling

        Returns:
            Node hash if a node was created, None otherwise
        """
        if value is None:
            # Handle null values - create node if no parent, otherwise skip
            if parent_node_id is None:
                properties = {"value": None, "_hash": self._generate_hash({"Null": None})}
                return self._create_node("Null", properties)
            return None

        if isinstance(value, dict):
            # Create node for object
            return self._process_object(value, parent_node_id, relationship_name, key_name)

        elif isinstance(value, list):
            # Create node for array
            return self._process_array(value, parent_node_id, relationship_name, key_name)

        else:
            # Primitive value - create node if no parent, otherwise add as property to parent
            if parent_node_id is None:
                # Root-level primitive, create a node for it
                properties = {
                    "value": value,
                    "_hash": self._generate_hash({key_name: value})
                }
                return self._create_node(key_name or "Primitive", properties)
            return None

    def _is_scalar_array(self, arr: List) -> bool:
        """
        Check if an array contains only scalar values (no nested objects or arrays).

        Args:
            arr: List to check

        Returns:
            True if array contains only scalars, False otherwise
        """
        if not isinstance(arr, list):
            return False

        for item in arr:
            if isinstance(item, (dict, list)):
                return False
        return True

    def _process_object(
        self,
        obj: Dict,
        parent_node_id: Optional[str],
        relationship_name: str,
        key_name: str,
    ) -> str:
        """
        Process a JSON object and create a node with properties.

        Args:
            obj: Dictionary object to process
            parent_node_id: Parent node hash
            relationship_name: Relationship type from parent
            key_name: Key name for node label

        Returns:
            Created node hash
        """
        # Separate primitive properties from nested structures
        properties = {}
        nested = {}

        for k, v in obj.items():
            if isinstance(v, list) and self._is_scalar_array(v):
                # Arrays of scalars should be stored as properties
                properties[k] = v
            elif isinstance(v, (dict, list)):
                nested[k] = v
            else:
                # Store primitive values as properties
                properties[k] = v

        # Smart labeling: use key name as label
        label = self._sanitize_label(key_name) if key_name else "Object"

        # Add hash for node matching
        node_hash = self._generate_hash({label: properties, "nested": nested})
        properties["_hash"] = node_hash

        # Create the node
        node_id = self._create_node(label, properties)

        # Create relationship from parent if exists
        if parent_node_id:
            self._create_relationship(parent_node_id, node_id, relationship_name)

        # Process nested structures
        for k, v in nested.items():
            self._process_value(v, node_id, k, k)

        return node_id

    def _process_array(
        self,
        arr: List,
        parent_node_id: Optional[str],
        relationship_name: str,
        key_name: str,
    ) -> str:
        """
        Process a JSON array and create nodes for elements.

        Args:
            arr: List to process
            parent_node_id: Parent node hash
            relationship_name: Relationship type from parent
            key_name: Key name for node label

        Returns:
            Created array node hash
        """
        # Create a container node for the array
        label = f"{self._sanitize_label(key_name)}Array" if key_name else "Array"

        properties = {
            "length": len(arr),
            "_hash": self._generate_hash({label: arr})
        }

        array_node_id = self._create_node(label, properties)

        # Create relationship from parent if exists
        if parent_node_id:
            self._create_relationship(parent_node_id, array_node_id, relationship_name)

        # Process each element in the array
        for idx, item in enumerate(arr):
            if isinstance(item, (dict, list)):
                # Create nodes for complex items
                item_label = f"{key_name}Item" if key_name else "Item"
                self._process_value(item, array_node_id, f"ELEMENT_{idx}", item_label)
            else:
                # For primitive values in array, create simple nodes
                item_properties = {
                    "value": item,
                    "index": idx,
                    "_hash": self._generate_hash({idx: item})
                }
                item_node_id = self._create_node("Primitive", item_properties)
                self._create_relationship(array_node_id, item_node_id, f"ELEMENT_{idx}")

        return array_node_id

    def _sanitize_label(self, label: str) -> str:
        """
        Sanitize label for use in Cypher queries.

        Args:
            label: Raw label string

        Returns:
            Sanitized label
        """
        # Remove special characters and spaces
        sanitized = ''.join(c if c.isalnum() or c == '_' else '_' for c in str(label))
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = 'L' + sanitized
        return sanitized or "Node"

    def _escape_string(self, value: str) -> str:
        """
        Escape string for safe use in Cypher queries.

        Args:
            value: String to escape

        Returns:
            Escaped string safe for Cypher
        """
        # Escape backslashes first to prevent double-escaping
        escaped = str(value).replace("\\", "\\\\")
        # Then escape single quotes
        escaped = escaped.replace("'", "\\'")
        return escaped

    def _format_value(self, value: Any) -> str:
        """Format a single value for Cypher."""
        if isinstance(value, str):
            return f"'{self._escape_string(value)}'"
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, (int, float)):
            return str(value)
        if value is None:
            return "null"
        return f"'{self._escape_string(str(value))}'"

    def _format_properties(self, properties: Dict[str, Any]) -> str:
        """
        Format properties dictionary for Cypher query.

        Args:
            properties: Properties dictionary

        Returns:
            Formatted properties string
        """
        if not properties:
            return "{}"

        props = []
        for key, value in properties.items():
            # Don't sanitize the special _hash property key - it needs to match exactly
            # in both node creation and relationship queries
            sanitized_key = key if key == "_hash" else self._sanitize_label(key)

            if isinstance(value, list):
                array_elements = [self._format_value(item) for item in value]
                props.append(f"{sanitized_key}: [{', '.join(array_elements)}]")
            else:
                props.append(f"{sanitized_key}: {self._format_value(value)}")

        return "{" + ", ".join(props) + "}"
