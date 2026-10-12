"""
Notification Dispatcher Service
Sends alerts (Discord webhook, Telegram, or Email) when high-potential leads are discovered.
"""
import os
import logging
from typing import Dict, Any, List
import httpx

logger = logging.getLogger(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class NotificationService:
    """Dispatches lead alerts to configured notification channels."""

    async def notify_new_lead(self, lead: Dict[str, Any]) -> bool:
        """
        Sends an alert about a promising new lead.
        """
        success = False
        message = (
            f"🚀 **New Qualified Startup Lead Discovered!**\n\n"
            f"**Company:** {lead.get('company_name')} ({lead.get('domain')})\n"
            f"**Website:** {lead.get('website_url')}\n"
            f"**Stage:** {lead.get('stage')}\n"
            f"**Summary:** {lead.get('summary')}\n\n"
            f"**Likely Needs:** {', '.join(lead.get('development_needs', []))}\n"
            f"**Why they qualify:** {lead.get('why_qualifies')}\n"
            f"**Score:** {int(lead.get('confidence_score', 0) * 100)}%"
        )

        # Discord alert
        if DISCORD_WEBHOOK_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(DISCORD_WEBHOOK_URL, json={"content": message})
                    if resp.status_code < 300:
                        success = True
            except Exception as e:
                logger.error(f"Failed to send Discord notification: {e}")

        # Telegram alert
        if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
            try:
                tg_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
                async with httpx.AsyncClient(timeout=10.0) as client:
                    resp = await client.post(tg_url, json={
                        "chat_id": TELEGRAM_CHAT_ID,
                        "text": message,
                        "parse_mode": "Markdown"
                    })
                    if resp.status_code < 300:
                        success = True
            except Exception as e:
                logger.error(f"Failed to send Telegram notification: {e}")

        if not DISCORD_WEBHOOK_URL and not TELEGRAM_BOT_TOKEN:
            logger.info(f"[Lead Alert - No webhook configured] New lead: {lead.get('company_name')} ({lead.get('domain')})")

        return success
