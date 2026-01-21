"""MCP tool generation from ontology classes."""

from typing import Any, Dict, List, Optional
from owlready2 import ThingClass, ObjectPropertyClass, DataPropertyClass
import structlog

logger = structlog.get_logger()


def generate_mcp_tools(
    ontology: Any, db_engine: Any, config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Generate MCP tools from ontology classes.
    
    Args:
        ontology: The loaded OWL ontology
        db_engine: SQLAlchemy engine for database queries
        config: Configuration dictionary
        
    Returns:
        List of MCP tool definitions
    """
    tools = []
    
    # Extract classes from ontology
    for cls in ontology.classes():
        if hasattr(cls, "name") and not cls.name.startswith("_"):
            tool = _create_tool_from_class(cls, db_engine, config)
            if tool:
                tools.append(tool)
    
    logger.info("Generated MCP tools", count=len(tools))
    return tools


def _create_tool_from_class(
    cls: ThingClass, db_engine: Any, config: Dict[str, Any]
) -> Optional[Dict[str, Any]]:
    """Create an MCP tool definition from an ontology class."""

    # Get table mapping from ontology annotations or config fallback
    table_name = _get_table_mapping(cls, config)
    if not table_name:
        logger.warning("Class has no table mapping", class_name=cls.name)
        return None

    # Get column mappings
    column_mappings = _get_column_mappings(cls, config)
    
    tool_name = f"query_{cls.name.lower()}"
    description = f"Query {cls.name} entities from the database using semantic queries"
    
    # Build tool schema
    tool_schema = {
        "name": tool_name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language query or SQL-like condition"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 10
                },
                "offset": {
                    "type": "integer",
                    "description": "Offset for pagination",
                    "default": 0
                }
            },
            "required": ["query"]
        }
    }
    
    # Store metadata for execution
    tool_schema["_metadata"] = {
        "class_name": cls.name,
        "table_name": table_name,
        "column_mappings": column_mappings,
        "db_engine": db_engine
    }
    
    return tool_schema


def _get_table_mapping(cls: ThingClass, config: Dict[str, Any] = None) -> Optional[str]:
    """Extract table name from ontology annotations or config fallback."""
    # Try ontology annotation first
    if hasattr(cls, "mapsToTable"):
        mapping = cls.mapsToTable
        if mapping:
            return str(mapping[0]) if isinstance(mapping, list) else str(mapping)

    # Fallback to config mappings
    if config:
        ontology_mappings = config.get("ontology_mappings", {})
        class_mappings = ontology_mappings.get("classes", {})
        if cls.name in class_mappings:
            return class_mappings[cls.name]

    return None


def _get_column_mappings(cls: ThingClass, config: Dict[str, Any] = None) -> Dict[str, str]:
    """Extract column mappings from class properties or config fallback."""
    mappings = {}

    # Fallback to config mappings first (more reliable)
    if config:
        ontology_mappings = config.get("ontology_mappings", {})
        column_mappings = ontology_mappings.get("columns", {})
        if cls.name in column_mappings:
            return column_mappings[cls.name]

    # Try ontology (may not work with all OWL formats)
    ontology = cls.namespace.ontology if hasattr(cls, 'namespace') else None
    if not ontology:
        return mappings

    for prop in ontology.data_properties():
        if hasattr(prop, 'domain') and cls in prop.domain:
            column_name = _get_column_mapping(prop)
            if column_name:
                mappings[prop.name] = column_name

    return mappings


def _get_column_mapping(prop: Any) -> Optional[str]:
    """Extract column name from property annotations."""
    if hasattr(prop, "mapsToColumn"):
        mapping = prop.mapsToColumn
        if mapping:
            return str(mapping[0]) if isinstance(mapping, list) else str(mapping)

    # Check for equivalent property (for renamed columns)
    if hasattr(prop, "equivalentProperty"):
        equiv = prop.equivalentProperty
        if hasattr(equiv, "mapsToColumn"):
            mapping = equiv.mapsToColumn
            if mapping:
                return str(mapping[0]) if isinstance(mapping, list) else str(mapping)

    return None


def translate_semantic_query_to_sql(
    query: str,
    table_name: str,
    column_mappings: Dict[str, str],
    limit: int = 10,
    offset: int = 0
) -> str:
    """
    Translate a semantic query to SQL.
    
    This is a simplified version. In production, you'd use NLP/LLM
    to better understand natural language queries.
    
    Args:
        query: Natural language or structured query
        table_name: Target database table
        column_mappings: Map of property names to column names
        limit: Maximum results
        offset: Pagination offset
        
    Returns:
        SQL query string
    """
    # Simple keyword-based translation
    query_lower = query.lower()
    
    # Build base SELECT
    columns = ", ".join(column_mappings.values()) or "*"
    sql = f"SELECT {columns} FROM {table_name}"
    
    # Add WHERE clause if query contains conditions
    if any(keyword in query_lower for keyword in ["where", "filter", "find"]):
        # This is simplified - in production, use NLP/LLM for parsing
        conditions = []
        for prop, col in column_mappings.items():
            if prop.lower() in query_lower:
                # Extract value (simplified)
                conditions.append(f"{col} LIKE '%{query}%'")
        
        if conditions:
            sql += " WHERE " + " OR ".join(conditions)
    
    # Add pagination
    sql += f" LIMIT {limit} OFFSET {offset}"
    
    return sql
