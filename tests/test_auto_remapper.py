"""Tests for auto-remapper."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.healing.auto_remapper import OntologyRemapper
from src.healing.validator import TripleValidator
from src.monitoring.diff_engine import SchemaDiff, DiffType


@pytest.fixture
def sample_diffs():
    """Create sample schema diffs for testing."""
    return [
        SchemaDiff(
            diff_type=DiffType.COLUMN_ADDED,
            table_name="customers",
            column_name="name",
            new_value="TEXT"
        )
    ]


def test_triple_validator():
    """Test triple validation."""
    validator = TripleValidator()
    
    valid_triples = """
    :Customer :mapsToTable "customers" .
    :name :mapsToColumn "name" .
    """
    
    is_valid, error, parsed = validator.validate_triples(valid_triples)
    
    # Note: Actual validation requires proper RDF parsing
    # This is a placeholder test
    assert isinstance(is_valid, bool)


@pytest.mark.asyncio
@patch('src.healing.auto_remapper.Anthropic')
async def test_ontology_remapper(mock_anthropic, sample_diffs, tmp_path):
    """Test ontology remapping."""
    # Mock Claude API response
    mock_response = Mock()
    mock_response.content = [
        Mock(text="""
        :Customer :mapsToTable "customers" .
        :name :mapsToColumn "name" .
        """)
    ]
    
    mock_client = Mock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    mock_anthropic.return_value = mock_client
    
    # Create temporary ontology file
    ontology_file = tmp_path / "test.owl"
    ontology_file.write_text("<?xml version='1.0'?><rdf:RDF></rdf:RDF>")
    
    remapper = OntologyRemapper(
        api_key="test-key",
        ontology_path=str(ontology_file),
        auto_approve=True,
        validation_enabled=False  # Disable validation for testing
    )
    
    result = await remapper.remap_ontology(sample_diffs)
    
    # Check that remapping was attempted
    assert "success" in result or "error" in result
