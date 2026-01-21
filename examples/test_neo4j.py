"""Test Neo4j adapter with MCP-style queries."""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.mcp_server.neo4j_adapter import Neo4jAdapter


async def test_neo4j():
    print("=" * 60)
    print("🔷 Neo4j MCP Adapter Test")
    print("=" * 60)

    # Initialize adapter
    print("\n[1] Connecting to Neo4j...")
    adapter = Neo4jAdapter(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="testpassword"
    )
    print("   ✅ Connected")

    # Test basic queries
    print("\n[2] Testing Basic Queries...")
    print("-" * 60)

    # Query all customers
    print("\n📝 Query: All customers")
    result = adapter.execute_query(
        label="Customer",
        query="all",
        column_mappings={"customerId": "id", "email": "email", "signupDate": "signup_date"},
        limit=10
    )
    if result["success"]:
        print(f"   ✅ Found {result['count']} customers")
        print(f"   Cypher: {result['cypher']}")
        for row in result["data"][:2]:
            print(f"   → {row}")
    else:
        print(f"   ❌ Error: {result['error']}")

    # Query all orders
    print("\n📝 Query: All orders")
    result = adapter.execute_query(
        label="Order",
        query="all",
        column_mappings={"orderId": "id", "orderDate": "order_date", "totalAmount": "total_amount"},
        limit=10
    )
    if result["success"]:
        print(f"   ✅ Found {result['count']} orders")
        print(f"   Cypher: {result['cypher']}")
        for row in result["data"][:2]:
            print(f"   → {row}")

    # Query with filter
    print("\n📝 Query: Active customers")
    result = adapter.execute_query(
        label="Customer",
        query="find where status active",
        column_mappings={"customerId": "id", "email": "email", "status": "status"},
        limit=10
    )
    if result["success"]:
        print(f"   ✅ Found {result['count']} active customers")
        for row in result["data"]:
            print(f"   → {row}")

    # Test graph-specific queries
    print("\n[3] Testing Graph Queries...")
    print("-" * 60)

    # Customer orders (graph traversal)
    print("\n📝 Graph Query: Customer 1's orders")
    result = adapter.execute_graph_query("customer_orders", {"customer_id": 1})
    if result["success"] and result["data"]:
        data = result["data"][0]
        print(f"   ✅ Customer: {data['customer_name']} ({data['customer_email']})")
        print(f"   Orders: {len(data['orders'])}")
        for order in data["orders"]:
            print(f"      → Order #{order['id']}: ${order['amount']} ({order['status']})")

    # Top customers by revenue
    print("\n📝 Graph Query: Top customers by revenue")
    result = adapter.execute_graph_query("top_customers", {"limit": 3})
    if result["success"]:
        print(f"   ✅ Top {len(result['data'])} customers:")
        for i, row in enumerate(result["data"], 1):
            print(f"      {i}. {row['customer']}: {row['order_count']} orders, ${row['total_spent']:.2f} total")

    # Revenue summary
    print("\n📝 Graph Query: Revenue summary")
    result = adapter.execute_graph_query("revenue_summary")
    if result["success"] and result["data"]:
        data = result["data"][0]
        print(f"   ✅ Total Orders: {data['total_orders']}")
        print(f"   ✅ Total Revenue: ${data['total_revenue']:.2f}")
        print(f"   ✅ Avg Order Value: ${data['avg_order_value']:.2f}")

    # Cleanup
    adapter.close()

    print("\n" + "=" * 60)
    print("✅ Neo4j Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_neo4j())
