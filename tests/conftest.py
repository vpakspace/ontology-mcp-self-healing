"""Pytest configuration and shared fixtures."""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Pytest configuration
pytest_plugins = []

# Markers for test categorization
pytest_configure = pytest.mark.parametrize(
    "slow", [False], indirect=True
)
