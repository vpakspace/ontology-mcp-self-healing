"""Schema monitoring for continuous database schema change detection."""

import asyncio
import hashlib
import json
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, inspect, MetaData, Table
from sqlalchemy.exc import SQLAlchemyError
import structlog
import yaml

from .diff_engine import SchemaDiffEngine, SchemaDiff, DiffType

logger = structlog.get_logger()


class SchemaMonitor:
    """
    Monitor database schema changes continuously.
    
    Uses SHA-256 hash-based change detection and generates detailed diffs
    when changes are detected.
    """
    
    def __init__(
        self,
        connection_string: str,
        check_interval: int = 60,
        detect_renames: bool = True,
        callback: Optional[Callable[[List[SchemaDiff]], None]] = None
    ):
        """
        Initialize schema monitor.
        
        Args:
            connection_string: Database connection string
            check_interval: Interval between checks in seconds
            detect_renames: Whether to detect renamed columns/tables
            callback: Function to call when changes are detected
        """
        self.connection_string = connection_string
        self.check_interval = check_interval
        self.detect_renames = detect_renames
        self.callback = callback
        
        self.engine = None
        self.current_schema: Dict[str, Dict[str, Any]] = {}
        self.schema_hash: Optional[str] = None
        self.diff_engine = SchemaDiffEngine(detect_renames=detect_renames)
        self.monitoring = False
        self._task: Optional[asyncio.Task] = None
        
        logger.info(
            "Schema monitor initialized",
            connection_string=connection_string,
            check_interval=check_interval
        )
    
    def start(self) -> None:
        """Start continuous schema monitoring."""
        if self.monitoring:
            logger.warning("Monitor already running")
            return
        
        # Connect to database
        self._connect()
        
        # Capture initial schema
        self.current_schema = self._capture_schema()
        self.schema_hash = self._compute_hash(self.current_schema)
        
        # Start monitoring loop
        self.monitoring = True
        self._task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("Schema monitoring started")
    
    def stop(self) -> None:
        """Stop schema monitoring."""
        self.monitoring = False
        if self._task:
            self._task.cancel()
        
        if self.engine:
            self.engine.dispose()
        
        logger.info("Schema monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_schema()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in monitoring loop", error=str(e))
                await asyncio.sleep(self.check_interval)  # Continue despite errors
    
    async def _check_schema(self) -> None:
        """Check for schema changes."""
        try:
            # Capture current schema
            new_schema = self._capture_schema()
            new_hash = self._compute_hash(new_schema)
            
            # Compare hashes
            if new_hash != self.schema_hash:
                logger.info("Schema change detected", hash=new_hash)
                
                # Compute diffs
                diffs = self.diff_engine.compute_diff(self.current_schema, new_schema)
                
                if diffs:
                    logger.info("Schema diffs computed", diff_count=len(diffs))
                    
                    # Update stored schema
                    self.current_schema = new_schema
                    self.schema_hash = new_hash
                    
                    # Trigger callback
                    if self.callback:
                        try:
                            if asyncio.iscoroutinefunction(self.callback):
                                await self.callback(diffs)
                            else:
                                self.callback(diffs)
                        except Exception as e:
                            logger.error("Callback error", error=str(e))
            else:
                logger.debug("No schema changes detected")
                
        except SQLAlchemyError as e:
            logger.error("Database error during schema check", error=str(e))
        except Exception as e:
            logger.error("Unexpected error during schema check", error=str(e))
    
    def _connect(self) -> None:
        """Connect to database."""
        try:
            self.engine = create_engine(self.connection_string, echo=False)
            logger.info("Database connected for monitoring")
        except Exception as e:
            logger.error("Failed to connect to database", error=str(e))
            raise
    
    def _capture_schema(self) -> Dict[str, Dict[str, Any]]:
        """Capture current database schema."""
        if not self.engine:
            raise RuntimeError("Database not connected")
        
        inspector = inspect(self.engine)
        schema = {}
        
        # Get all table names
        table_names = inspector.get_table_names()
        
        for table_name in table_names:
            columns = {}
            
            # Get column information
            for column in inspector.get_columns(table_name):
                col_name = column["name"]
                col_type = str(column["type"])
                columns[col_name] = col_type
            
            schema[table_name] = columns
        
        return schema
    
    def _compute_hash(self, schema: Dict[str, Dict[str, Any]]) -> str:
        """Compute SHA-256 hash of schema."""
        # Serialize schema to JSON
        schema_json = json.dumps(schema, sort_keys=True)
        
        # Compute hash
        hash_obj = hashlib.sha256(schema_json.encode())
        return hash_obj.hexdigest()
    
    def get_current_schema(self) -> Dict[str, Dict[str, Any]]:
        """Get current captured schema."""
        return self.current_schema.copy()
    
    def get_schema_hash(self) -> Optional[str]:
        """Get current schema hash."""
        return self.schema_hash


def main():
    """Main entry point for schema monitor."""
    import argparse
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    parser = argparse.ArgumentParser(description="Monitor database schema changes")
    parser.add_argument("--config", default="config/config.yaml", help="Config file path")
    parser.add_argument("--interval", type=int, default=60, help="Check interval in seconds")
    
    args = parser.parse_args()
    
    # Load config
    with open(args.config, "r") as f:
        config = yaml.safe_load(f)
    
    db_config = config.get("database", {})
    connection_string = db_config.get("connection_string", "sqlite:///./test_database.db")
    
    # Create monitor
    def on_change(diffs: List[SchemaDiff]):
        print(f"Schema changes detected: {len(diffs)} changes")
        for diff in diffs:
            print(f"  - {diff.diff_type.value}: {diff.table_name}.{diff.column_name}")
    
    monitor = SchemaMonitor(
        connection_string=connection_string,
        check_interval=args.interval,
        callback=on_change
    )
    
    # Start monitoring
    try:
        monitor.start()
        print("Schema monitoring started. Press Ctrl+C to stop.")
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping schema monitor...")
        monitor.stop()


if __name__ == "__main__":
    main()
