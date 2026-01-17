"""MCP Server module for ontology-based tool generation."""

from .server import OntologyMCPServer
from .tools import generate_mcp_tools

__all__ = ["OntologyMCPServer", "generate_mcp_tools"]
