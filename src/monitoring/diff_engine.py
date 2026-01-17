"""Schema diff engine for detecting and analyzing database schema changes."""

from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger()


class DiffType(Enum):
    """Type of schema change."""
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    TABLE_RENAMED = "table_renamed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_RENAMED = "column_renamed"
    COLUMN_TYPE_CHANGED = "column_type_changed"
    INDEX_ADDED = "index_added"
    INDEX_REMOVED = "index_removed"


@dataclass
class SchemaDiff:
    """Represents a single schema change."""
    diff_type: DiffType
    table_name: str
    column_name: Optional[str] = None
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    detected_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert diff to dictionary."""
        return {
            "diff_type": self.diff_type.value,
            "table_name": self.table_name,
            "column_name": self.column_name,
            "old_value": str(self.old_value) if self.old_value else None,
            "new_value": str(self.new_value) if self.new_value else None,
            "detected_at": self.detected_at.isoformat()
        }


class SchemaDiffEngine:
    """Engine for computing schema differences."""
    
    def __init__(self, detect_renames: bool = True):
        """
        Initialize the diff engine.
        
        Args:
            detect_renames: Whether to attempt detecting column/table renames
        """
        self.detect_renames = detect_renames
        logger.info("Schema diff engine initialized", detect_renames=detect_renames)
    
    def compute_diff(
        self,
        old_schema: Dict[str, Dict[str, Any]],
        new_schema: Dict[str, Dict[str, Any]]
    ) -> List[SchemaDiff]:
        """
        Compute differences between two schemas.
        
        Args:
            old_schema: Previous schema state {table_name: {column_name: type}}
            new_schema: Current schema state {table_name: {column_name: type}}
            
        Returns:
            List of schema differences
        """
        diffs = []
        
        old_tables = set(old_schema.keys())
        new_tables = set(new_schema.keys())
        
        # Find added tables
        for table in new_tables - old_tables:
            diffs.append(SchemaDiff(
                diff_type=DiffType.TABLE_ADDED,
                table_name=table,
                new_value="added"
            ))
        
        # Find removed tables
        for table in old_tables - new_tables:
            diffs.append(SchemaDiff(
                diff_type=DiffType.TABLE_REMOVED,
                table_name=table,
                old_value="removed"
            ))
        
        # Find renamed tables (heuristic)
        if self.detect_renames:
            renamed_tables = self._detect_renamed_tables(
                old_tables - new_tables,
                new_tables - old_tables
            )
            for old_name, new_name in renamed_tables:
                diffs.append(SchemaDiff(
                    diff_type=DiffType.TABLE_RENAMED,
                    table_name=old_name,
                    old_value=old_name,
                    new_value=new_name
                ))
                old_tables.remove(old_name)
                new_tables.remove(new_name)
        
        # Compare columns in common tables
        common_tables = old_tables & new_tables
        for table in common_tables:
            table_diffs = self._compare_table_schema(
                table, old_schema[table], new_schema[table]
            )
            diffs.extend(table_diffs)
        
        logger.info("Schema diff computed", diff_count=len(diffs))
        return diffs
    
    def _compare_table_schema(
        self,
        table_name: str,
        old_columns: Dict[str, Any],
        new_columns: Dict[str, Any]
    ) -> List[SchemaDiff]:
        """Compare columns within a single table."""
        diffs = []
        
        old_col_names = set(old_columns.keys())
        new_col_names = set(new_columns.keys())
        
        # Find added columns
        for col in new_col_names - old_col_names:
            diffs.append(SchemaDiff(
                diff_type=DiffType.COLUMN_ADDED,
                table_name=table_name,
                column_name=col,
                new_value=new_columns[col]
            ))
        
        # Find removed columns
        for col in old_col_names - new_col_names:
            diffs.append(SchemaDiff(
                diff_type=DiffType.COLUMN_REMOVED,
                table_name=table_name,
                column_name=col,
                old_value=old_columns[col]
            ))
        
        # Detect renamed columns (heuristic)
        if self.detect_renames:
            renamed_cols = self._detect_renamed_columns(
                table_name,
                old_col_names - new_col_names,
                new_col_names - old_col_names
            )
            for old_name, new_name in renamed_cols:
                diffs.append(SchemaDiff(
                    diff_type=DiffType.COLUMN_RENAMED,
                    table_name=table_name,
                    column_name=old_name,
                    old_value=old_name,
                    new_value=new_name
                ))
                old_col_names.remove(old_name)
                new_col_names.remove(new_name)
        
        # Compare column types
        common_cols = old_col_names & new_col_names
        for col in common_cols:
            if old_columns[col] != new_columns[col]:
                diffs.append(SchemaDiff(
                    diff_type=DiffType.COLUMN_TYPE_CHANGED,
                    table_name=table_name,
                    column_name=col,
                    old_value=old_columns[col],
                    new_value=new_columns[col]
                ))
        
        return diffs
    
    def _detect_renamed_tables(
        self,
        removed_tables: set,
        added_tables: set
    ) -> List[tuple]:
        """Attempt to detect renamed tables using heuristics."""
        renamed = []
        
        # Simple heuristic: tables with similar names might be renames
        # In production, use more sophisticated algorithms (Levenshtein distance, etc.)
        for old_table in list(removed_tables):
            best_match = None
            best_score = 0.5  # Threshold
            
            for new_table in added_tables:
                # Simple similarity check
                score = self._similarity_score(old_table.lower(), new_table.lower())
                if score > best_score:
                    best_score = score
                    best_match = new_table
            
            if best_match:
                renamed.append((old_table, best_match))
                added_tables.remove(best_match)
        
        return renamed
    
    def _detect_renamed_columns(
        self,
        table_name: str,
        removed_cols: set,
        added_cols: set
    ) -> List[tuple]:
        """Attempt to detect renamed columns using heuristics."""
        renamed = []
        
        for old_col in list(removed_cols):
            best_match = None
            best_score = 0.5  # Threshold
            
            for new_col in added_cols:
                score = self._similarity_score(old_col.lower(), new_col.lower())
                if score > best_score:
                    best_score = score
                    best_match = new_col
            
            if best_match:
                renamed.append((old_col, best_match))
                added_cols.remove(best_match)
        
        return renamed
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Compute similarity score between two strings."""
        # Simple implementation - in production, use Levenshtein distance
        if str1 == str2:
            return 1.0
        
        # Check if one contains the other
        if str1 in str2 or str2 in str1:
            return 0.7
        
        # Check character overlap
        common_chars = set(str1) & set(str2)
        if common_chars:
            return len(common_chars) / max(len(str1), len(str2))
        
        return 0.0
