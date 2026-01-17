"""Self-healing orchestration system."""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import yaml
import structlog

from ..monitoring.schema_monitor import SchemaMonitor
from ..monitoring.diff_engine import SchemaDiff
from ..healing.auto_remapper import OntologyRemapper
from ..mcp_server.server import OntologyMCPServer
from .alerts import AlertManager

logger = structlog.get_logger()


class SelfHealingAgentSystem:
    """
    Orchestrates the self-healing workflow.
    
    Monitors schema changes, analyzes them, and automatically heals
    the ontology using Claude API.
    """
    
    def __init__(
        self,
        config_path: str = "config/config.yaml",
        audit_log_path: str = "logs/audit.json"
    ):
        """
        Initialize self-healing system.
        
        Args:
            config_path: Path to configuration file
            audit_log_path: Path to audit log file
        """
        self.config = self._load_config(config_path)
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.schema_monitor: Optional[SchemaMonitor] = None
        self.ontology_remapper: Optional[OntologyRemapper] = None
        self.mcp_server: Optional[OntologyMCPServer] = None
        self.alert_manager: Optional[AlertManager] = None
        
        self._initialize_components()
        
        logger.info("Self-healing system initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        config_file = Path(config_path)
        if not config_file.exists():
            logger.warning("Config file not found, using defaults", path=config_path)
            return self._default_config()
        
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _default_config(self) -> Dict[str, Any]:
        """Return default configuration."""
        return {
            "monitoring": {"enabled": True, "check_interval": 60},
            "healing": {"enabled": True, "auto_approve": False},
            "alerts": {"enabled": True},
            "database": {"connection_string": "sqlite:///./test_database.db"},
            "ontology": {"main_file": "ontologies/business_domain.owl"}
        }
    
    def _initialize_components(self) -> None:
        """Initialize system components."""
        # Initialize schema monitor
        if self.config.get("monitoring", {}).get("enabled", True):
            db_config = self.config.get("database", {})
            connection_string = db_config.get("connection_string", "sqlite:///./test_database.db")
            
            monitor_config = self.config.get("monitoring", {})
            check_interval = monitor_config.get("check_interval", 60)
            detect_renames = monitor_config.get("detect_renames", True)
            
            self.schema_monitor = SchemaMonitor(
                connection_string=connection_string,
                check_interval=check_interval,
                detect_renames=detect_renames,
                callback=self._on_schema_change
            )
        
        # Initialize ontology remapper
        if self.config.get("healing", {}).get("enabled", True):
            import os
            from dotenv import load_dotenv
            
            load_dotenv()
            
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                logger.warning("ANTHROPIC_API_KEY not found in environment")
            
            healing_config = self.config.get("healing", {})
            ontology_config = self.config.get("ontology", {})
            
            self.ontology_remapper = OntologyRemapper(
                api_key=api_key or "",
                model=healing_config.get("claude_model", "claude-3-5-sonnet-20241022"),
                temperature=healing_config.get("temperature", 0.3),
                ontology_path=ontology_config.get("main_file", "ontologies/business_domain.owl"),
                auto_approve=healing_config.get("auto_approve", False),
                validation_enabled=healing_config.get("validation_enabled", True)
            )
            
            # Set approval callback
            if not healing_config.get("auto_approve", False):
                self.ontology_remapper.set_approval_callback(self._request_approval)
        
        # Initialize MCP server
        ontology_config = self.config.get("ontology", {})
        ontology_file = ontology_config.get("main_file", "ontologies/business_domain.owl")
        
        if Path(ontology_file).exists():
            self.mcp_server = OntologyMCPServer()
        
        # Initialize alert manager
        if self.config.get("alerts", {}).get("enabled", True):
            alerts_config = self.config.get("alerts", {})
            import os
            webhook_url = os.getenv("ALERT_WEBHOOK_URL") or alerts_config.get("webhook_url")
            
            self.alert_manager = AlertManager(
                enabled=True,
                webhook_url=webhook_url,
                slack_channel=alerts_config.get("slack_channel"),
                teams_channel=alerts_config.get("teams_channel")
            )
    
    async def _on_schema_change(self, diffs: List[SchemaDiff]) -> None:
        """
        Callback when schema changes are detected.
        
        Args:
            diffs: List of schema differences
        """
        logger.info("Schema change detected", diff_count=len(diffs))
        
        # Log to audit log
        await self._log_audit_event("schema_change_detected", {"diffs": [d.to_dict() for d in diffs]})
        
        # Send alert
        if self.alert_manager:
            await self.alert_manager.send_schema_change_alert(diffs)
        
        # Trigger healing if enabled
        if self.config.get("healing", {}).get("enabled", True) and self.ontology_remapper:
            await self._heal_ontology(diffs)
    
    async def _heal_ontology(self, diffs: List[SchemaDiff]) -> None:
        """
        Heal ontology based on schema changes.
        
        Args:
            diffs: List of schema differences
        """
        logger.info("Starting ontology healing", diff_count=len(diffs))
        
        # Get current ontology
        current_ontology = None
        if self.mcp_server:
            current_ontology = self.mcp_server.ontology
        
        # Attempt remapping
        result = await self.ontology_remapper.remap_ontology(diffs, current_ontology)
        
        # Log result
        await self._log_audit_event("healing_attempted", {
            "diffs": [d.to_dict() for d in diffs],
            "result": result
        })
        
        # Send alert
        if self.alert_manager:
            await self.alert_manager.send_healing_alert(
                result.get("success", False),
                diffs,
                result
            )
        
        # Reload MCP server if healing was successful
        if result.get("success", False) and self.mcp_server:
            try:
                self.mcp_server.reload_ontology()
                logger.info("MCP server reloaded after healing")
                await self._log_audit_event("mcp_server_reloaded", {"result": "success"})
            except Exception as e:
                logger.error("Failed to reload MCP server", error=str(e))
                await self._log_audit_event("mcp_server_reload_failed", {"error": str(e)})
    
    def _request_approval(self, triples: str, diffs: List[SchemaDiff]) -> bool:
        """
        Request manual approval for ontology changes.
        
        Args:
            triples: Proposed RDF triples
            diffs: Schema differences
            
        Returns:
            True if approved, False otherwise
        """
        logger.info("Requesting approval for ontology changes")
        
        # In production, this would show a UI or send notification
        # For now, default to True if auto_approve is disabled
        # User can override this method
        
        print("\n" + "="*60)
        print("ONTOLOGY UPDATE APPROVAL REQUESTED")
        print("="*60)
        print(f"\nSchema Changes ({len(diffs)}):")
        for diff in diffs:
            print(f"  - {diff.diff_type.value}: {diff.table_name}.{diff.column_name or 'N/A'}")
        
        print(f"\nProposed Triples:\n{triples}")
        print("\n" + "="*60)
        
        # Default to auto-approve for demo
        # In production, implement actual approval mechanism
        return True
    
    async def _log_audit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Log event to audit log."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        # Append to audit log
        with open(self.audit_log_path, "a") as f:
            f.write(json.dumps(event) + "\n")
        
        logger.info("Audit event logged", event_type=event_type)
    
    def start(self) -> None:
        """Start the self-healing system."""
        logger.info("Starting self-healing system")
        
        if self.schema_monitor:
            self.schema_monitor.start()
        
        logger.info("Self-healing system started")
    
    def stop(self) -> None:
        """Stop the self-healing system."""
        logger.info("Stopping self-healing system")
        
        if self.schema_monitor:
            self.schema_monitor.stop()
        
        if self.mcp_server:
            self.mcp_server.close()
        
        logger.info("Self-healing system stopped")
    
    async def run_forever(self) -> None:
        """Run the system forever."""
        self.start()
        
        try:
            logger.info("Self-healing system running. Press Ctrl+C to stop.")
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down self-healing system")
            self.stop()


def main():
    """Main entry point for self-healing system."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Self-healing ontology MCP agent system")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--audit-log", default="logs/audit.json", help="Audit log path")
    
    args = parser.parse_args()
    
    # Initialize system
    system = SelfHealingAgentSystem(
        config_path=args.config,
        audit_log_path=args.audit_log
    )
    
    # Run forever
    try:
        asyncio.run(system.run_forever())
    except KeyboardInterrupt:
        print("\nShutting down...")


if __name__ == "__main__":
    main()
