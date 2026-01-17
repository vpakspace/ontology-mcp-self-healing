"""Comprehensive tests for schema diff engine."""

import pytest
from datetime import datetime
from src.monitoring.diff_engine import (
    SchemaDiffEngine,
    SchemaDiff,
    DiffType
)


@pytest.fixture
def diff_engine():
    """Create diff engine instance."""
    return SchemaDiffEngine(detect_renames=True)


@pytest.fixture
def old_schema():
    """Sample old schema."""
    return {
        "customers": {
            "id": "INTEGER",
            "email": "TEXT",
            "signup_date": "TEXT"
        },
        "orders": {
            "id": "INTEGER",
            "customer_id": "INTEGER",
            "total_amount": "REAL"
        }
    }


@pytest.fixture
def new_schema():
    """Sample new schema."""
    return {
        "customers": {
            "id": "INTEGER",
            "email": "TEXT",
            "signup_date": "TEXT",
            "name": "TEXT"  # Added
        },
        "orders": {
            "id": "INTEGER",
            "customer_id": "INTEGER",
            "total_amount": "REAL"
        }
    }


def test_compute_diff_column_added(diff_engine, old_schema, new_schema):
    """Test detecting added columns."""
    diffs = diff_engine.compute_diff(old_schema, new_schema)
    
    assert len(diffs) > 0
    assert any(diff.diff_type == DiffType.COLUMN_ADDED for diff in diffs)
    assert any(diff.column_name == "name" for diff in diffs)


def test_compute_diff_column_removed(diff_engine, old_schema, new_schema):
    """Test detecting removed columns."""
    # Swap schemas
    diffs = diff_engine.compute_diff(new_schema, old_schema)
    
    assert len(diffs) > 0
    assert any(diff.diff_type == DiffType.COLUMN_REMOVED for diff in diffs)
    assert any(diff.column_name == "name" for diff in diffs)


def test_compute_diff_table_added(diff_engine, old_schema):
    """Test detecting added tables."""
    new_schema = old_schema.copy()
    new_schema["products"] = {"id": "INTEGER", "name": "TEXT"}
    
    diffs = diff_engine.compute_diff(old_schema, new_schema)
    
    assert len(diffs) > 0
    assert any(diff.diff_type == DiffType.TABLE_ADDED for diff in diffs)
    assert any(diff.table_name == "products" for diff in diffs)


def test_compute_diff_table_removed(diff_engine, old_schema):
    """Test detecting removed tables."""
    new_schema = {"customers": old_schema["customers"]}  # Remove orders
    
    diffs = diff_engine.compute_diff(old_schema, new_schema)
    
    assert len(diffs) > 0
    assert any(diff.diff_type == DiffType.TABLE_REMOVED for diff in diffs)
    assert any(diff.table_name == "orders" for diff in diffs)


def test_compute_diff_column_type_changed(diff_engine, old_schema):
    """Test detecting column type changes."""
    new_schema = old_schema.copy()
    new_schema["customers"]["id"] = "TEXT"  # Changed type
    
    diffs = diff_engine.compute_diff(old_schema, new_schema)
    
    assert len(diffs) > 0
    assert any(diff.diff_type == DiffType.COLUMN_TYPE_CHANGED for diff in diffs)
    assert any(diff.column_name == "id" and diff.table_name == "customers" for diff in diffs)


def test_compute_diff_no_changes(diff_engine, old_schema):
    """Test when no changes are detected."""
    diffs = diff_engine.compute_diff(old_schema, old_schema)
    
    assert len(diffs) == 0


def test_schema_diff_to_dict():
    """Test SchemaDiff serialization."""
    diff = SchemaDiff(
        diff_type=DiffType.COLUMN_ADDED,
        table_name="customers",
        column_name="name",
        new_value="TEXT",
        detected_at=datetime(2024, 1, 1, 12, 0, 0)
    )
    
    result = diff.to_dict()
    
    assert result["diff_type"] == "column_added"
    assert result["table_name"] == "customers"
    assert result["column_name"] == "name"
    assert result["new_value"] == "TEXT"
    assert "detected_at" in result


def test_similarity_score():
    """Test similarity score calculation."""
    engine = SchemaDiffEngine()
    
    # Identical strings
    assert engine._similarity_score("customer_id", "customer_id") == 1.0
    
    # Similar strings
    assert engine._similarity_score("customer_id", "customerId") > 0.0
    
    # Different strings
    assert engine._similarity_score("customer_id", "order_id") < 1.0


def test_detect_renames_disabled():
    """Test diff engine with rename detection disabled."""
    engine = SchemaDiffEngine(detect_renames=False)
    
    old_schema = {"customers": {"old_name": "TEXT"}}
    new_schema = {"customers": {"new_name": "TEXT"}}
    
    diffs = engine.compute_diff(old_schema, new_schema)
    
    # Should detect as removal and addition, not rename
    assert any(diff.diff_type == DiffType.COLUMN_REMOVED for diff in diffs)
    assert any(diff.diff_type == DiffType.COLUMN_ADDED for diff in diffs)
    # Should NOT detect as rename
    assert not any(diff.diff_type == DiffType.COLUMN_RENAMED for diff in diffs)
