"""Multi-agent coordination example."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_server.server import OntologyMCPServer
from src.agents.examples.analytics_agent import AnalyticsAgent
from src.agents.examples.support_agent import SupportAgent
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run multi-agent demo."""
    print("="*60)
    print("Self-Healing Ontology MCP Agent System - Multi-Agent Demo")
    print("="*60)
    
    # Initialize MCP Server
    print("\n[1/3] Initializing MCP Server...")
    try:
        mcp_server = OntologyMCPServer()
        print(f"✓ MCP Server initialized with {len(mcp_server.get_tools())} tools")
    except Exception as e:
        print(f"✗ Failed to initialize MCP Server: {e}")
        return
    
    # Create multiple agents
    print("\n[2/3] Creating agents...")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        print("⚠ ANTHROPIC_API_KEY not set - agents require API key")
        print("  Set it in .env file or environment variable")
        return
    
    try:
        analytics_agent = AnalyticsAgent(mcp_server, claude_api_key=api_key)
        print(f"✓ Created: {analytics_agent.name}")
        
        support_agent = SupportAgent(mcp_server, claude_api_key=api_key)
        print(f"✓ Created: {support_agent.name}")
        
    except Exception as e:
        print(f"✗ Failed to create agents: {e}")
        return
    
    # Demonstrate agent coordination
    print("\n[3/3] Demonstrating agent coordination...")
    print("\nExample queries:")
    
    # Analytics agent queries
    print("\n--- Analytics Agent Queries ---")
    queries = [
        "What are the total sales for the last month?",
        "Show me the top 5 customers by order value",
        "Generate a report of all orders"
    ]
    
    for query in queries[:1]:  # Just show one for demo
        print(f"\nQuery: {query}")
        try:
            response = await analytics_agent.query(query)
            print(f"Response: {response[:200]}...")  # Truncate for display
        except Exception as e:
            print(f"Error: {e}")
    
    # Support agent queries
    print("\n--- Support Agent Queries ---")
    support_queries = [
        "Find all orders for customer with email alice@example.com",
        "What is the status of order #123?",
        "Show me customer signup information"
    ]
    
    for query in support_queries[:1]:  # Just show one for demo
        print(f"\nQuery: {query}")
        try:
            response = await support_agent.query(query)
            print(f"Response: {response[:200]}...")  # Truncate for display
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "="*60)
    print("Multi-agent demo complete!")
    print("\nNote: Agents share the same MCP server and ontology,")
    print("      ensuring consistent semantic understanding across agents.")
    print("="*60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
