"""Twilio SMS/MMS.

Signature validation is implemented here rather than pulled from the Twilio
SDK - it is fifteen lines of HMAC and this webhook is publicly reachable, so
it is worth being able to read the check that protects it.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
from urllib.parse import urlencode

import requests

from ..config import Config
from ..router import Media

log = logging.getLogger("moneybot.twilio")

API_ROOT = "https://api.twilio.com/2010-04-01"


def validate_signature(auth_token: str, url: str, params: dict[str, str], signature: str) -> bool:
    """Twilio's scheme: the full URL, then every POST param sorted by name and
    concatenated as key+value, HMAC-SHA1'd with the auth token."""
    if not auth_token or not signature:
        return False
    payload = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    digest = hmac.new(auth_token.encode("utf-8"), payload.encode("utf-8"), hashlib.sha1).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def twiml(text: str) -> str:
    escaped = (
        text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{escaped}</Message></Response>'


class TwilioSMS:
    name = "sms"

    def __init__(self, config: Config):
        self.config = config

    @property
    def configured(self) -> bool:
        return bool(
            self.config.twilio_account_sid and self.config.twilio_auth_token and self.config.twilio_from
        )

    def send(self, to: str, text: str) -> bool:
        if not self.configured:
            log.error("Twilio is not configured; message not sent")
            return False
        url = f"{API_ROOT}/Accounts/{self.config.twilio_account_sid}/Messages.json"
        try:
            response = requests.post(
                url,
                data=urlencode({"To": to, "From": self.config.twilio_from, "Body": text}),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                auth=(self.config.twilio_account_sid, self.config.twilio_auth_token),
                timeout=20,
            )
        except requests.RequestException as exc:
            log.error("Twilio send failed: %s", exc)
            return False
        if response.status_code >= 300:
            log.error("Twilio send rejected (%s): %s", response.status_code, response.text[:300])
            return False
        return True

    def fetch_media(self, media_url: str, content_type: str) -> Media | None:
        """MMS media lives behind the account's basic auth."""
        try:
            response = requests.get(
                media_url,
                auth=(self.config.twilio_account_sid, self.config.twilio_auth_token),
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            log.warning("could not fetch MMS media: %s", exc)
            return None
        return Media(
            data=response.content,
            media_type=response.headers.get("Content-Type", content_type),
        )

    def media_from_form(self, form: dict[str, str]) -> list[Media]:
        count = int(form.get("NumMedia", "0") or 0)
        out = []
        for index in range(count):
            url = form.get(f"MediaUrl{index}")
            ctype = form.get(f"MediaContentType{index}", "image/jpeg")
            if not url:
                continue
            media = self.fetch_media(url, ctype)
            if media:
                out.append(media)
        return out
