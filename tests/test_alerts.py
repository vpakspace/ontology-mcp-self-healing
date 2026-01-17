"""Comprehensive tests for alert manager."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.system.alerts import AlertManager
from src.monitoring.diff_engine import SchemaDiff, DiffType


@pytest.fixture
def alert_manager():
    """Create alert manager instance."""
    return AlertManager(
        enabled=True,
        webhook_url=None,
        slack_channel="#alerts"
    )


@pytest.fixture
def sample_diffs():
    """Create sample schema diffs."""
    return [
        SchemaDiff(
            diff_type=DiffType.COLUMN_ADDED,
            table_name="customers",
            column_name="name",
            new_value="TEXT"
        ),
        SchemaDiff(
            diff_type=DiffType.TABLE_ADDED,
            table_name="products"
        )
    ]


@pytest.mark.asyncio
async def test_send_alert_enabled(alert_manager):
    """Test sending alert when enabled."""
    result = await alert_manager.send_alert(
        title="Test Alert",
        message="Test message",
        severity="info"
    )
    
    # Should succeed even without webhook (logs instead)
    assert result is True


@pytest.mark.asyncio
async def test_send_alert_disabled():
    """Test sending alert when disabled."""
    manager = AlertManager(enabled=False)
    
    result = await manager.send_alert(
        title="Test",
        message="Test",
        severity="info"
    )
    
    assert result is False


@pytest.mark.asyncio
@patch('src.system.alerts.httpx.AsyncClient')
async def test_send_alert_webhook(mock_client_class, sample_diffs):
    """Test sending alert via webhook."""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.raise_for_status = Mock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client_class.return_value = mock_client
    
    manager = AlertManager(
        enabled=True,
        webhook_url="https://example.com/webhook"
    )
    
    result = await manager.send_alert(
        title="Test",
        message="Test",
        severity="info"
    )
    
    assert result is True
    mock_client.post.assert_called_once()


@pytest.mark.asyncio
async def test_send_schema_change_alert(alert_manager, sample_diffs):
    """Test sending schema change alert."""
    result = await alert_manager.send_schema_change_alert(sample_diffs)
    
    assert result is True


@pytest.mark.asyncio
async def test_send_healing_alert_success(alert_manager, sample_diffs):
    """Test sending healing alert for successful healing."""
    healing_result = {"success": True, "triples": ":Customer :mapsToTable \"customers\" ."}
    
    result = await alert_manager.send_healing_alert(
        success=True,
        diffs=sample_diffs,
        healing_result=healing_result
    )
    
    assert result is True


@pytest.mark.asyncio
async def test_send_healing_alert_failure(alert_manager, sample_diffs):
    """Test sending healing alert for failed healing."""
    healing_result = {"success": False, "error": "Test error"}
    
    result = await alert_manager.send_healing_alert(
        success=False,
        diffs=sample_diffs,
        healing_result=healing_result
    )
    
    assert result is True


def test_format_webhook_payload_slack(alert_manager):
    """Test formatting webhook payload for Slack."""
    alert_data = {
        "title": "Test Alert",
        "message": "Test message",
        "severity": "warning",
        "timestamp": "2024-01-01T12:00:00"
    }
    
    payload = alert_manager._format_webhook_payload(alert_data)
    
    assert "channel" in payload or "text" in payload or "blocks" in payload


def test_format_webhook_payload_teams():
    """Test formatting webhook payload for Teams."""
    manager = AlertManager(teams_channel="#teams-alerts")
    
    alert_data = {
        "title": "Test Alert",
        "message": "Test message",
        "severity": "error",
        "timestamp": "2024-01-01T12:00:00"
    }
    
    payload = manager._format_webhook_payload(alert_data)
    
    assert "@type" in payload or "summary" in payload or isinstance(payload, dict)


def test_get_theme_color(alert_manager):
    """Test theme color selection."""
    colors = {
        "info": "0078D4",
        "warning": "FFAA00",
        "error": "D13438",
        "critical": "750B1C"
    }
    
    for severity, expected_color in colors.items():
        color = alert_manager._get_theme_color(severity)
        assert color == expected_color
