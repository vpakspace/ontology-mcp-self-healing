"""MCP Server implementation for ontology-based queries."""

import asyncio
import json
import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from owlready2 import get_ontology, sync_reasoner_pellet
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
import structlog
import yaml

from .tools import generate_mcp_tools, translate_semantic_query_to_sql

logger = structlog.get_logger()


class OntologyMCPServer:
    """
    MCP Server that loads ontologies and generates tools for semantic queries.
    
    This server bridges semantic queries (using OWL ontologies) with SQL databases,
    automatically translating ontology-based queries to SQL.
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the MCP server with configuration."""
        self.config = self._load_config(config_path)
        self.ontology = None
        self.db_engine = None
        self.tools: List[Dict[str, Any]] = []
        self._cache: Dict[str, Any] = {}
        
        # Load ontology and database
        self._load_ontology()
        self._connect_database()
        self._generate_tools()
        
        logger.info("MCP Server initialized", config=config_path)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning("Config file not found, using defaults", path=config_path)
            return self._default_config()
        
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        
        # Handle environment variable substitution
        config_str = json.dumps(config)
        for key, value in config.items():
            if isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                env_var = value[2:-1]
                env_value = os.getenv(env_var, "")
                config_str = config_str.replace(value, env_value)
        
        return json.loads(config_str) if config_str != json.dumps(config) else config
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "ontology": {"main_file": "ontologies/business_domain.owl"},
            "database": {"connection_string": "sqlite:///./test_database.db"},
            "mcp_server": {"enable_caching": True, "cache_ttl": 300}
        }
    
    def _load_ontology(self) -> None:
        """Load OWL ontology from file."""
        ontology_path = Path(self.config.get("ontology", {}).get("main_file", "ontologies/business_domain.owl"))
        
        if not ontology_path.exists():
            logger.error("Ontology file not found", path=str(ontology_path))
            raise FileNotFoundError(f"Ontology file not found: {ontology_path}")
        
        logger.info("Loading ontology", path=str(ontology_path))
        self.ontology = get_ontology(f"file://{ontology_path.absolute()}").load()
        
        # Run reasoner if needed (optional)
        # sync_reasoner_pellet(self.ontology, infer_property_values=True)
        
        logger.info("Ontology loaded", classes=len(list(self.ontology.classes())))
    
    def _connect_database(self) -> None:
        """Connect to database using SQLAlchemy."""
        db_config = self.config.get("database", {})
        connection_string = db_config.get("connection_string", "sqlite:///./test_database.db")

        # Create engine - use simpler config for SQLite
        if connection_string.startswith("sqlite"):
            self.db_engine = create_engine(connection_string, echo=False)
        else:
            # Create engine with connection pooling for other databases
            pool_size = db_config.get("pool_size", 10)
            max_overflow = db_config.get("max_overflow", 20)

            self.db_engine = create_engine(
                connection_string,
                poolclass=QueuePool,
                pool_size=pool_size,
                pool_pre_ping=True,
                echo=False
            )

        logger.info("Database connected", connection_string=connection_string)
    
    def _generate_tools(self) -> None:
        """Generate MCP tools from ontology classes."""
        self.tools = generate_mcp_tools(self.ontology, self.db_engine, self.config)
        logger.info("Tools generated", count=len(self.tools))
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an MCP tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            
        Returns:
            Tool execution result
        """
        # Find tool
        tool = next((t for t in self.tools if t["name"] == tool_name), None)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")
        
        metadata = tool.get("_metadata", {})
        table_name = metadata["table_name"]
        column_mappings = metadata["column_mappings"]
        
        # Check cache if enabled
        cache_key = f"{tool_name}:{json.dumps(arguments, sort_keys=True)}"
        if self.config.get("mcp_server", {}).get("enable_caching", True):
            cached_result = self._cache.get(cache_key)
            if cached_result:
                logger.info("Cache hit", tool=tool_name)
                return cached_result
        
        # Translate query to SQL
        query = arguments.get("query", "")
        limit = arguments.get("limit", 10)
        offset = arguments.get("offset", 0)
        
        sql = translate_semantic_query_to_sql(
            query, table_name, column_mappings, limit, offset
        )
        
        # Execute SQL
        try:
            with self.db_engine.connect() as conn:
                result = conn.execute(text(sql))
                rows = result.fetchall()
                
                # Convert rows to dictionaries
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in rows]
                
                result_dict = {
                    "success": True,
                    "data": data,
                    "count": len(data),
                    "sql": sql
                }
                
                # Cache result
                if self.config.get("mcp_server", {}).get("enable_caching", True):
                    cache_ttl = self.config.get("mcp_server", {}).get("cache_ttl", 300)
                    self._cache[cache_key] = result_dict
                    # In production, implement TTL-based cache expiration
                
                logger.info("Tool executed", tool=tool_name, row_count=len(data))
                return result_dict
                
        except Exception as e:
            logger.error("Tool execution failed", tool=tool_name, error=str(e))
            return {
                "success": False,
                "error": str(e),
                "sql": sql
            }
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools."""
        # Return tools without internal metadata
        return [
            {k: v for k, v in tool.items() if not k.startswith("_")}
            for tool in self.tools
        ]
    
    def reload_ontology(self) -> None:
        """Reload ontology and regenerate tools (for hot-reload)."""
        logger.info("Reloading ontology")
        self._load_ontology()
        self._generate_tools()
        self._cache.clear()
        logger.info("Ontology reloaded")
    
    def close(self) -> None:
        """Close database connections."""
        if self.db_engine:
            self.db_engine.dispose()
            logger.info("Database connections closed")


def main():
    """Main entry point for MCP server."""
    import os
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Initialize server
    server = OntologyMCPServer()
    
    # Keep running (in production, integrate with MCP protocol)
    try:
        logger.info("MCP Server running. Press Ctrl+C to stop.")
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down MCP server")
        server.close()


if __name__ == "__main__":
    import os
    main()
