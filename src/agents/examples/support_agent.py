"""Customer support agent example."""

from typing import Optional
from ..base_agent import BaseAgent
from ...mcp_server.server import OntologyMCPServer

class SupportAgent(BaseAgent):
    """Agent for customer support queries."""
    
    def __init__(
        self,
        mcp_server: OntologyMCPServer,
        claude_api_key: Optional[str] = None
    ):
        """
        Initialize support agent.
        
        Args:
            mcp_server: MCP server instance
            claude_api_key: Anthropic API key (optional)
        """
        super().__init__(
            name="SupportAgent",
            description="An AI agent specialized in customer support. "
                       "I can query customer data, order history, and other "
                       "information to help resolve customer issues quickly.",
            mcp_server=mcp_server,
            claude_api_key=claude_api_key,
            model="claude-3-5-sonnet-20241022",
            temperature=0.5  # Moderate temperature for conversational support
        )
