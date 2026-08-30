"""Telegram bot channel.

Kept alongside SMS because photos are free here and MMS is not. Same router,
same ledger - only the transport differs.
"""

from __future__ import annotations

import logging
import time

import requests

from ..config import Config
from ..router import Inbound, Media, Router

log = logging.getLogger("moneybot.telegram")


class Telegram:
    name = "telegram"

    def __init__(self, config: Config):
        self.config = config

    @property
    def configured(self) -> bool:
        return bool(self.config.telegram_token)

    @property
    def _api(self) -> str:
        return f"https://api.telegram.org/bot{self.config.telegram_token}"

    def send(self, to: str, text: str) -> bool:
        if not self.configured:
            log.error("Telegram token missing; message not sent")
            return False
        try:
            response = requests.post(
                f"{self._api}/sendMessage",
                json={"chat_id": to, "text": text, "disable_web_page_preview": True},
                timeout=20,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            log.error("Telegram send failed: %s", exc)
            return False
        return True

    def download(self, file_id: str) -> bytes | None:
        try:
            info = requests.get(f"{self._api}/getFile", params={"file_id": file_id}, timeout=20)
            info.raise_for_status()
            path = info.json()["result"]["file_path"]
            blob = requests.get(
                f"https://api.telegram.org/file/bot{self.config.telegram_token}/{path}", timeout=60
            )
            blob.raise_for_status()
            return blob.content
        except (requests.RequestException, KeyError) as exc:
            log.warning("Telegram file download failed: %s", exc)
            return None

    def to_inbound(self, update: dict) -> Inbound | None:
        message = update.get("message") or update.get("edited_message")
        if not message:
            return None
        chat_id = str(message.get("chat", {}).get("id", ""))
        text = message.get("text") or message.get("caption") or ""
        media: list[Media] = []

        photos = message.get("photo") or []
        if photos:
            largest = max(photos, key=lambda p: p.get("file_size", 0))
            data = self.download(largest["file_id"])
            if data:
                media.append(Media(data=data, media_type="image/jpeg"))

        document = message.get("document")
        if document:
            mime = document.get("mime_type", "")
            if mime in ("application/pdf",) or mime.startswith("image/"):
                data = self.download(document["file_id"])
                if data:
                    media.append(
                        Media(data=data, media_type=mime, filename=document.get("file_name"))
                    )

        if not text and not media:
            return None
        return Inbound(channel="telegram", party=chat_id, text=text, media=media)

    def poll_forever(self, router: Router, interval: float = 1.0) -> None:
        """Long-poll loop for local development and single-instance hosting."""
        offset = None
        while True:
            try:
                response = requests.get(
                    f"{self._api}/getUpdates",
                    params={"timeout": 30, **({"offset": offset} if offset else {})},
                    timeout=45,
                )
                response.raise_for_status()
                for update in response.json().get("result", []):
                    offset = update["update_id"] + 1
                    inbound = self.to_inbound(update)
                    if inbound is None:
                        continue
                    self.send(inbound.party, router.handle(inbound))
            except requests.RequestException as exc:
                log.warning("poll error: %s", exc)
                time.sleep(5)
            except KeyboardInterrupt:  # pragma: no cover
                return
            time.sleep(interval)
