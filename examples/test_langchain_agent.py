"""Test LangChain agent with natural language queries."""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.agents.base_agent import BaseAgent
from src.mcp_server.server import OntologyMCPServer


async def test_langchain_agent():
    print("=" * 60)
    print("🤖 LangChain Agent Test - Natural Language Queries")
    print("=" * 60)

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found!")
        return

    print(f"\n[1] API Key: {'*' * 20}...{api_key[-8:]}")

    # Initialize MCP server
    print("\n[2] Initializing MCP Server...")
    mcp_server = OntologyMCPServer()
    tools = mcp_server.get_tools()
    print(f"   Available tools: {[t['name'] for t in tools]}")

    # Initialize agent
    print("\n[3] Initializing LangChain Agent...")
    agent = BaseAgent(
        name="Database Assistant",
        description="You help users query customer and order data using semantic queries.",
        mcp_server=mcp_server,
        claude_api_key=api_key,
        model="claude-sonnet-4-20250514"
    )
    print("   ✅ Agent initialized")

    # Test natural language queries
    test_queries = [
        "Show me all customers",
        "List all orders",
        "How many orders do we have?",
        "What is the total amount of all orders?",
    ]

    print("\n[4] Testing Natural Language Queries...")
    print("-" * 60)

    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Query {i}: \"{query}\"")
        try:
            result = await agent.query(query)
            print(f"   ✅ Response: {result[:200]}..." if len(str(result)) > 200 else f"   ✅ Response: {result}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Cleanup
    mcp_server.close()

    print("\n" + "=" * 60)
    print("✅ LangChain Agent Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_langchain_agent())
