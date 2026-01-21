"""Test LangChain agent with Neo4j backend."""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_anthropic import ChatAnthropic
from src.mcp_server.neo4j_adapter import Neo4jAdapter
import json


def create_neo4j_tools(adapter: Neo4jAdapter):
    """Create LangChain tools from Neo4j adapter."""

    def query_customer(query: str) -> str:
        """Query customers from Neo4j graph database."""
        result = adapter.execute_query(
            label="Customer",
            query=query,
            column_mappings={"id": "id", "email": "email", "name": "name", "status": "status"},
            limit=10
        )
        if result["success"]:
            return f"Found {result['count']} customers: {json.dumps(result['data'], indent=2)}"
        return f"Error: {result.get('error')}"

    def query_order(query: str) -> str:
        """Query orders from Neo4j graph database."""
        result = adapter.execute_query(
            label="Order",
            query=query,
            column_mappings={"id": "id", "order_date": "order_date", "total_amount": "total_amount", "status": "status"},
            limit=10
        )
        if result["success"]:
            return f"Found {result['count']} orders: {json.dumps(result['data'], indent=2)}"
        return f"Error: {result.get('error')}"

    def query_customer_orders(customer_id: str) -> str:
        """Get all orders for a specific customer (graph traversal)."""
        try:
            cid = int(customer_id)
        except:
            cid = 1
        result = adapter.execute_graph_query("customer_orders", {"customer_id": cid})
        if result["success"] and result["data"]:
            return json.dumps(result["data"], indent=2)
        return f"Error: {result.get('error', 'No data')}"

    def query_top_customers(limit: str = "5") -> str:
        """Get top customers by total revenue."""
        try:
            lim = int(limit)
        except:
            lim = 5
        result = adapter.execute_graph_query("top_customers", {"limit": lim})
        if result["success"]:
            return f"Top customers: {json.dumps(result['data'], indent=2)}"
        return f"Error: {result.get('error')}"

    def query_revenue_summary(query: str = "") -> str:
        """Get total revenue summary."""
        result = adapter.execute_graph_query("revenue_summary")
        if result["success"]:
            return json.dumps(result["data"], indent=2)
        return f"Error: {result.get('error')}"

    return [
        Tool(name="query_customer", description="Query customers from Neo4j database", func=query_customer),
        Tool(name="query_order", description="Query orders from Neo4j database", func=query_order),
        Tool(name="query_customer_orders", description="Get all orders for a specific customer ID (graph traversal)", func=query_customer_orders),
        Tool(name="query_top_customers", description="Get top customers by total spending", func=query_top_customers),
        Tool(name="query_revenue_summary", description="Get total revenue summary", func=query_revenue_summary),
    ]


async def test_neo4j_agent():
    print("=" * 60)
    print("🔷🤖 Neo4j + LangChain Agent Test")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY not found!")
        return

    # Initialize Neo4j adapter
    print("\n[1] Connecting to Neo4j...")
    adapter = Neo4jAdapter(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="testpassword"
    )
    print("   ✅ Connected")

    # Create tools
    print("\n[2] Creating LangChain tools...")
    tools = create_neo4j_tools(adapter)
    print(f"   ✅ Created {len(tools)} tools:")
    for tool in tools:
        print(f"      📦 {tool.name}")

    # Create LLM and agent
    print("\n[3] Initializing LangChain Agent...")
    llm = ChatAnthropic(
        anthropic_api_key=api_key,
        model_name="claude-sonnet-4-20250514",
        temperature=0.3
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Neo4j Graph Database Assistant. You help users query a graph database containing Customer and Order nodes with PLACED relationships.

Available tools:
- query_customer: Query all customers or filter by status
- query_order: Query all orders
- query_customer_orders: Get orders for a specific customer (uses graph traversal)
- query_top_customers: Get customers ranked by total spending
- query_revenue_summary: Get overall revenue statistics

Use graph queries when exploring relationships between customers and orders."""),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    print("   ✅ Agent initialized")

    # Test queries
    print("\n[4] Testing Natural Language Queries...")
    print("-" * 60)

    queries = [
        "Who are the top 3 customers by spending?",
        "What orders has customer Alice placed?",
        "What's the total revenue?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n📝 Query {i}: \"{query}\"")
        try:
            result = await executor.ainvoke({
                "input": query,
                "chat_history": []
            })
            output = result.get("output", "No response")
            # Handle list output
            if isinstance(output, list) and output:
                text = output[0].get('text', str(output)) if isinstance(output[0], dict) else str(output)
            else:
                text = str(output)
            print(f"   ✅ {text[:300]}...")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Cleanup
    adapter.close()

    print("\n" + "=" * 60)
    print("✅ Neo4j Agent Test Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_neo4j_agent())
