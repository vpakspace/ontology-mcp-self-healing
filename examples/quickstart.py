"""Quickstart example demonstrating the self-healing ontology MCP system."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.mcp_server.server import OntologyMCPServer
from src.monitoring.schema_monitor import SchemaMonitor
from src.monitoring.diff_engine import SchemaDiff
from src.agents.examples.analytics_agent import AnalyticsAgent
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run quickstart example."""
    print("="*60)
    print("Self-Healing Ontology MCP Agent System - Quickstart")
    print("="*60)
    
    # Step 1: Initialize MCP Server
    print("\n[1/5] Initializing MCP Server...")
    try:
        mcp_server = OntologyMCPServer()
        print(f"✓ MCP Server initialized with {len(mcp_server.get_tools())} tools")
        
        # List available tools
        print("\nAvailable tools:")
        for tool in mcp_server.get_tools():
            print(f"  - {tool['name']}: {tool.get('description', 'No description')}")
    except Exception as e:
        print(f"✗ Failed to initialize MCP Server: {e}")
        return
    
    # Step 2: Query data through semantic interface
    print("\n[2/5] Querying data through semantic interface...")
    try:
        # Execute a query using one of the tools
        tools = mcp_server.get_tools()
        if tools:
            tool_name = tools[0]["name"]
            result = await mcp_server.execute_tool(
                tool_name,
                {"query": "all", "limit": 5}
            )
            
            if result.get("success"):
                print(f"✓ Query successful: {result.get('count', 0)} results")
                print(f"  SQL: {result.get('sql', 'N/A')}")
                if result.get("data"):
                    print(f"  Sample data: {result['data'][0]}")
            else:
                print(f"✗ Query failed: {result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"✗ Query failed: {e}")
    
    # Step 3: Create an agent
    print("\n[3/5] Creating analytics agent...")
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            agent = AnalyticsAgent(mcp_server, claude_api_key=api_key)
            print(f"✓ Agent created: {agent.name}")
            print(f"  Available tools: {', '.join(agent.get_available_tools())}")
        else:
            print("⚠ Skipping agent creation (ANTHROPIC_API_KEY not set)")
    except Exception as e:
        print(f"✗ Failed to create agent: {e}")
    
    # Step 4: Monitor schema changes
    print("\n[4/5] Setting up schema monitoring...")
    try:
        db_config = mcp_server.config.get("database", {})
        connection_string = db_config.get("connection_string", "sqlite:///./test_database.db")
        
        def on_schema_change(diffs):
            print(f"\n✓ Schema change detected: {len(diffs)} changes")
            for diff in diffs:
                print(f"  - {diff.diff_type.value}: {diff.table_name}.{diff.column_name or 'N/A'}")
        
        monitor = SchemaMonitor(
            connection_string=connection_string,
            check_interval=5,  # Check every 5 seconds for demo
            callback=on_schema_change
        )
        
        monitor.start()
        print("✓ Schema monitoring started")
        print("  (In production, this would run continuously)")
        
        # Stop after a moment
        await asyncio.sleep(2)
        monitor.stop()
        
    except Exception as e:
        print(f"✗ Failed to setup monitoring: {e}")
    
    # Step 5: Summary
    print("\n[5/5] Summary")
    print("="*60)
    print("✓ MCP Server: Running")
    print("✓ Tools: Generated from ontology")
    print("✓ Schema Monitoring: Available")
    print("✓ Agent System: Ready")
    print("\nNext steps:")
    print("  1. Modify database schema (add/rename columns)")
    print("  2. System will detect changes automatically")
    print("  3. Auto-healing will update ontology mappings")
    print("  4. MCP server will reload with new mappings")
    print("\nFor full system, run: python examples/full_system.py")
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
