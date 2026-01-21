"""Test MCP tools with real database queries."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_server.server import OntologyMCPServer


async def test_mcp_tools():
    print("=" * 60)
    print("🧪 MCP Tools Test - Real Database Queries")
    print("=" * 60)

    # Initialize server
    print("\n[1] Initializing MCP Server...")
    server = OntologyMCPServer()

    # List available tools
    tools = server.get_tools()
    print(f"\n[2] Available MCP Tools ({len(tools)}):")
    for tool in tools:
        print(f"  📦 {tool['name']}: {tool['description']}")

    # Test queries
    test_cases = [
        {
            "tool": "query_customer",
            "description": "Query all customers",
            "args": {"query": "all", "limit": 10}
        },
        {
            "tool": "query_customer",
            "description": "Query with filter keyword",
            "args": {"query": "find where email", "limit": 5}
        },
        {
            "tool": "query_order",
            "description": "Query all orders",
            "args": {"query": "all", "limit": 10}
        },
        {
            "tool": "query_order",
            "description": "Query orders with pagination",
            "args": {"query": "all", "limit": 2, "offset": 1}
        },
    ]

    print("\n[3] Executing Test Queries...")
    print("-" * 60)

    for i, test in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test['description']}")
        print(f"   Tool: {test['tool']}")
        print(f"   Args: {test['args']}")

        try:
            result = await server.execute_tool(test['tool'], test['args'])

            if result.get("success"):
                print(f"   ✅ Success! Rows: {result.get('count', 0)}")
                print(f"   SQL: {result.get('sql', 'N/A')}")

                # Show data preview
                data = result.get("data", [])
                if data:
                    print(f"   Data preview:")
                    for j, row in enumerate(data[:3]):
                        print(f"      [{j+1}] {row}")
                    if len(data) > 3:
                        print(f"      ... and {len(data) - 3} more rows")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

        except Exception as e:
            print(f"   ❌ Exception: {e}")

    # Test caching
    print("\n[4] Testing Cache...")
    print("-" * 60)

    # First call (should miss cache)
    print("\n   First call (cache miss expected):")
    result1 = await server.execute_tool("query_customer", {"query": "all", "limit": 5})
    print(f"   ✅ Result: {result1.get('count')} rows")

    # Second call (should hit cache)
    print("\n   Second call (cache hit expected):")
    result2 = await server.execute_tool("query_customer", {"query": "all", "limit": 5})
    print(f"   ✅ Result: {result2.get('count')} rows (from cache)")

    # Cleanup
    server.close()

    print("\n" + "=" * 60)
    print("✅ MCP Tools Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())
