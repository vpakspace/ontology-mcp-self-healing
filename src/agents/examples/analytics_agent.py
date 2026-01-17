"""Analytics agent example."""

from typing import Optional
from ..base_agent import BaseAgent
from ...mcp_server.server import OntologyMCPServer

class AnalyticsAgent(BaseAgent):
    """Agent for analytics and reporting queries."""
    
    def __init__(
        self,
        mcp_server: OntologyMCPServer,
        claude_api_key: Optional[str] = None
    ):
        """
        Initialize analytics agent.
        
        Args:
            mcp_server: MCP server instance
            claude_api_key: Anthropic API key (optional)
        """
        super().__init__(
            name="AnalyticsAgent",
            description="An AI agent specialized in analytics and reporting. "
                       "I can query databases using semantic queries to generate "
                       "reports, analyze trends, and answer business questions.",
            mcp_server=mcp_server,
            claude_api_key=claude_api_key,
            model="claude-3-5-sonnet-20241022",
            temperature=0.2  # Lower temperature for more focused analytics
        )
