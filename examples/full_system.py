"""Full system deployment example."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.system.self_healing import SelfHealingAgentSystem
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    """Run full system example."""
    print("="*60)
    print("Self-Healing Ontology MCP Agent System - Full Deployment")
    print("="*60)
    
    # Initialize full system
    print("\nInitializing self-healing system...")
    
    try:
        system = SelfHealingAgentSystem(
            config_path="config/config.yaml",
            audit_log_path="logs/audit.json"
        )
        
        print("✓ System initialized")
        print("\nSystem components:")
        print(f"  - Schema Monitor: {'✓' if system.schema_monitor else '✗'}")
        print(f"  - Ontology Remapper: {'✓' if system.ontology_remapper else '✗'}")
        print(f"  - MCP Server: {'✓' if system.mcp_server else '✗'}")
        print(f"  - Alert Manager: {'✓' if system.alert_manager else '✗'}")
        
        print("\nStarting system...")
        print("Press Ctrl+C to stop")
        print("="*60)
        
        # Run forever
        await system.run_forever()
        
    except KeyboardInterrupt:
        print("\n\nShutting down system...")
        system.stop()
        print("System stopped")
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
