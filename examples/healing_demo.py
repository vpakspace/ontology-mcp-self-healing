"""Self-healing demo - full cycle with Claude AI"""
import asyncio
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.system.self_healing import SelfHealingAgentSystem
from src.monitoring.diff_engine import SchemaDiff, DiffType
from dotenv import load_dotenv

load_dotenv()


async def demo_healing():
    print("="*60)
    print("🔧 Self-Healing Demo - Full Cycle with Claude AI")
    print("="*60)

    # Initialize system
    print("\n[1] Initializing self-healing system...")
    system = SelfHealingAgentSystem()

    print(f"  ✓ Schema Monitor: {'Ready' if system.schema_monitor else 'N/A'}")
    print(f"  ✓ Ontology Remapper: {'Ready' if system.ontology_remapper else 'N/A'}")
    print(f"  ✓ MCP Server: {'Ready' if system.mcp_server else 'N/A'}")

    # Simulate schema change detection
    print("\n[2] Simulating schema change: customers.phone added...")

    # Create a diff representing the phone column addition
    diff = SchemaDiff(
        diff_type=DiffType.COLUMN_ADDED,
        table_name="customers",
        column_name="phone",
        old_value=None,
        new_value="TEXT"
    )

    print(f"  📝 Change: {diff.diff_type.value} - {diff.table_name}.{diff.column_name}")

    # Trigger healing
    print("\n[3] Triggering AI-powered ontology healing...")
    print("  🤖 Calling Claude API to generate new mappings...")

    if system.ontology_remapper:
        result = await system.ontology_remapper.remap_ontology(
            [diff],
            system.mcp_server.ontology if system.mcp_server else None
        )

        print(f"\n[4] Healing result:")
        if result.get("success"):
            print("  ✅ SUCCESS!")
            triples = result.get('triples', 'N/A')
            print(f"  📄 Generated triples:")
            print("-" * 40)
            print(triples[:800] if len(triples) > 800 else triples)
            print("-" * 40)
            if result.get("backup_path"):
                print(f"  💾 Backup saved: {result.get('backup_path')}")
            if result.get("ontology_path"):
                print(f"  📁 Ontology updated: {result.get('ontology_path')}")
        else:
            print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
            if result.get('triples'):
                print(f"  📄 Proposed triples:")
                print("-" * 40)
                print(result.get('triples', '')[:500])
                print("-" * 40)
    else:
        print("  ⚠️ Ontology remapper not available")

    # Show what would happen next
    print("\n[5] Next steps in production:")
    print("  → MCP Server would reload with new ontology")
    print("  → New tool 'phone' mapping would be available")
    print("  → Agents would use updated semantic queries")
    print("  → Alert would be sent to Slack/Teams")

    print("\n" + "="*60)
    print("Demo complete!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(demo_healing())
