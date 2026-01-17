"""Utility tests and helper functions."""

import pytest
import json
from pathlib import Path
import tempfile


class TestUtils:
    """Utility functions for tests."""
    
    @staticmethod
    def create_temp_ontology(content: str) -> str:
        """Create a temporary ontology file."""
        ontology_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.owl')
        ontology_path = ontology_file.name
        ontology_file.write(content)
        ontology_file.close()
        return ontology_path
    
    @staticmethod
    def create_temp_config(db_path: str, ontology_path: str) -> str:
        """Create a temporary config file."""
        config_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.yaml')
        config_path = config_file.name
        
        config_content = f"""
database:
  connection_string: sqlite:///{db_path}

ontology:
  main_file: {ontology_path}

monitoring:
  enabled: true
  check_interval: 60

healing:
  enabled: true
  auto_approve: false

alerts:
  enabled: false
"""
        config_file.write(config_content)
        config_file.close()
        return config_path
    
    @staticmethod
    def load_json_file(file_path: str) -> dict:
        """Load JSON file."""
        with open(file_path, 'r') as f:
            return json.load(f)


def test_utils_create_temp_ontology():
    """Test temporary ontology creation."""
    content = "<?xml version='1.0'?><rdf:RDF></rdf:RDF>"
    path = TestUtils.create_temp_ontology(content)
    
    assert Path(path).exists()
    assert Path(path).read_text() == content
    
    # Cleanup
    Path(path).unlink()


def test_utils_load_json_file(tmp_path):
    """Test JSON file loading."""
    json_file = tmp_path / "test.json"
    json_file.write_text('{"test": "value"}')
    
    data = TestUtils.load_json_file(str(json_file))
    assert data == {"test": "value"}
