# Test Suite

Comprehensive test suite for the Self-Healing Ontology MCP Agent System.

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_mcp_server.py -v
```

### Run Tests with Coverage
```bash
pytest tests/ --cov=src --cov-report=html
```

### Run Only Unit Tests
```bash
pytest tests/ -m unit -v
```

### Run Only Integration Tests
```bash
pytest tests/ -m integration -v
```

### Run Tests Excluding Slow Tests
```bash
pytest tests/ -m "not slow" -v
```

## Test Structure

- `test_mcp_server.py` - MCP server tests
- `test_tools.py` - Tool generation tests
- `test_schema_monitor.py` - Schema monitoring tests
- `test_diff_engine.py` - Diff computation tests
- `test_validator.py` - Triple validation tests
- `test_auto_remapper.py` - Auto-remapping tests
- `test_alerts.py` - Alert system tests
- `test_agents.py` - Agent system tests
- `test_self_healing.py` - Self-healing system tests
- `test_integration.py` - Integration tests
- `test_utils.py` - Utility function tests
- `conftest.py` - Pytest configuration and fixtures

## Test Coverage

The test suite covers:

✅ MCP server initialization and tool generation
✅ Schema monitoring and change detection
✅ Diff engine (all diff types)
✅ Triple validation
✅ Auto-remapping with Claude API (mocked)
✅ Alert system
✅ Agent creation and queries
✅ Self-healing orchestration
✅ Integration scenarios

## Fixtures

Common fixtures are defined in `conftest.py`:
- Database fixtures
- Ontology fixtures
- Config fixtures
- Mock objects

## Mocking

Tests use mocks for:
- Anthropic Claude API calls
- HTTP webhook requests
- LangChain agent execution
- Database connections (where appropriate)

## Notes

- Some tests may be skipped if dependencies aren't available
- Integration tests require proper setup (database, ontology files)
- Async tests use `pytest.mark.asyncio`
- Tests clean up temporary files automatically

## Continuous Integration

Tests are designed to run in CI/CD pipelines:
- Fast execution (< 5 minutes)
- No external dependencies required (mocked)
- Deterministic results
- Proper cleanup
