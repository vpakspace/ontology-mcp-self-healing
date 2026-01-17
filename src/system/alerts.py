"""Alert management for schema changes and healing events."""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import httpx
import structlog

from ..monitoring.diff_engine import SchemaDiff

logger = structlog.get_logger()


class AlertManager:
    """Manages alerts and webhooks for schema changes."""
    
    def __init__(
        self,
        enabled: bool = True,
        webhook_url: Optional[str] = None,
        slack_channel: Optional[str] = None,
        teams_channel: Optional[str] = None
    ):
        """
        Initialize alert manager.
        
        Args:
            enabled: Whether alerts are enabled
            webhook_url: Webhook URL for alerts (Slack/Teams)
            slack_channel: Slack channel for alerts
            teams_channel: Teams channel for alerts
        """
        self.enabled = enabled
        self.webhook_url = webhook_url
        self.slack_channel = slack_channel
        self.teams_channel = teams_channel
        
        logger.info(
            "Alert manager initialized",
            enabled=enabled,
            webhook_url=webhook_url
        )
    
    async def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "info",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send an alert.
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            metadata: Additional metadata
            
        Returns:
            True if alert sent successfully
        """
        if not self.enabled:
            logger.debug("Alerts disabled, skipping")
            return False
        
        alert_data = {
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {}
        }
        
        # Send to webhook if configured
        if self.webhook_url:
            try:
                await self._send_webhook(alert_data)
                logger.info("Alert sent", title=title, severity=severity)
                return True
            except Exception as e:
                logger.error("Failed to send alert", error=str(e))
                return False
        
        # Log alert if no webhook configured
        logger.info("Alert generated", title=title, severity=severity, message=message)
        return True
    
    async def send_schema_change_alert(
        self,
        diffs: List[SchemaDiff]
    ) -> bool:
        """
        Send alert for schema changes.
        
        Args:
            diffs: List of schema differences
            
        Returns:
            True if alert sent successfully
        """
        title = f"Schema Change Detected: {len(diffs)} changes"
        
        # Build message
        message_parts = []
        for diff in diffs:
            if diff.column_name:
                message_parts.append(f"{diff.diff_type.value}: {diff.table_name}.{diff.column_name}")
            else:
                message_parts.append(f"{diff.diff_type.value}: {diff.table_name}")
        
        message = "\n".join(message_parts)
        
        # Determine severity
        severity = "warning"
        critical_types = ["TABLE_REMOVED", "COLUMN_REMOVED"]
        if any(diff.diff_type.value in critical_types for diff in diffs):
            severity = "error"
        
        metadata = {
            "diff_count": len(diffs),
            "diffs": [diff.to_dict() for diff in diffs]
        }
        
        return await self.send_alert(title, message, severity, metadata)
    
    async def send_healing_alert(
        self,
        success: bool,
        diffs: List[SchemaDiff],
        healing_result: Dict[str, Any]
    ) -> bool:
        """
        Send alert for healing events.
        
        Args:
            success: Whether healing was successful
            diffs: List of schema differences that triggered healing
            healing_result: Result from healing operation
            
        Returns:
            True if alert sent successfully
        """
        if success:
            title = "Ontology Auto-Healing Successful"
            message = f"Successfully remapped ontology for {len(diffs)} schema changes"
            severity = "info"
        else:
            title = "Ontology Auto-Healing Failed"
            message = healing_result.get("error", "Unknown error")
            severity = "error"
        
        metadata = {
            "healing_result": healing_result,
            "diff_count": len(diffs)
        }
        
        return await self.send_alert(title, message, severity, metadata)
    
    async def _send_webhook(self, alert_data: Dict[str, Any]) -> None:
        """Send alert to webhook URL."""
        if not self.webhook_url:
            return
        
        # Format payload based on webhook type (Slack/Teams)
        payload = self._format_webhook_payload(alert_data)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
    
    def _format_webhook_payload(
        self,
        alert_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format alert data for webhook (Slack/Teams format)."""
        
        severity_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "❌",
            "critical": "🚨"
        }
        
        emoji = severity_emoji.get(alert_data["severity"], "ℹ️")
        
        # Slack format
        if self.slack_channel or "slack" in (self.webhook_url or "").lower():
            return {
                "channel": self.slack_channel or "#alerts",
                "text": f"{emoji} {alert_data['title']}",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*{alert_data['title']}*\n{alert_data['message']}"
                        }
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": f"Severity: {alert_data['severity']} | Time: {alert_data['timestamp']}"
                            }
                        ]
                    }
                ]
            }
        
        # Teams format
        if self.teams_channel or "teams" in (self.webhook_url or "").lower():
            return {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": self._get_theme_color(alert_data["severity"]),
                "summary": alert_data["title"],
                "sections": [
                    {
                        "activityTitle": alert_data["title"],
                        "activitySubtitle": alert_data["message"],
                        "facts": [
                            {
                                "name": "Severity",
                                "value": alert_data["severity"]
                            },
                            {
                                "name": "Time",
                                "value": alert_data["timestamp"]
                            }
                        ]
                    }
                ]
            }
        
        # Generic JSON format
        return alert_data
    
    def _get_theme_color(self, severity: str) -> str:
        """Get theme color for Teams message card."""
        colors = {
            "info": "0078D4",
            "warning": "FFAA00",
            "error": "D13438",
            "critical": "750B1C"
        }
        return colors.get(severity, "0078D4")
