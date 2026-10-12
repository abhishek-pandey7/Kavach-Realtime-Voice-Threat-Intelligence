"""Family alerts over Telegram (free, no KYC).

Setup: create a bot with @BotFather, send it a message from the family
member's account, then put these in .env:
    TELEGRAM_BOT_TOKEN=...
    TELEGRAM_CHAT_ID=...   (from https://api.telegram.org/bot<token>/getUpdates)
Without them, alerts are only logged.
"""

import logging
import os

import httpx

log = logging.getLogger(__name__)


class TelegramAlerter:
    def __init__(self, token: str | None = None, chat_id: str | None = None,
                 transport: httpx.AsyncBaseTransport | None = None):
        self.token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")
        self._transport = transport

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    async def send(self, text: str) -> bool:
        if not self.enabled:
            log.warning("Family alert (Telegram not configured):\n%s", text)
            return False
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        async with httpx.AsyncClient(timeout=10, transport=self._transport) as http:
            try:
                resp = await http.post(url, json={"chat_id": self.chat_id, "text": text})
                resp.raise_for_status()
                return True
            except httpx.HTTPError as exc:
                log.warning("Telegram alert failed: %r", exc)
                return False


def format_alert(scam_type: str, risk: int, flags: list[tuple[str, str]], last_lines: list[str]) -> str:
    """A short, plain alert for a family member's phone."""
    kind = scam_type.replace("_", " ") if scam_type and scam_type != "none" else "possible scam"
    lines = [f"Kavach alert: {kind} call in progress (risk {risk}/100).", ""]
    if flags:
        lines.append("Why:")
        lines.extend(f"- {category.replace('_', ' ')}: \"{evidence}\"" for category, evidence in flags[:5])
        lines.append("")
    if last_lines:
        lines.append("Last words heard:")
        lines.extend(f"> {line}" for line in last_lines[-3:])
        lines.append("")
    lines.append("Kavach has warned them. Please call them now.")
    return "\n".join(lines)
