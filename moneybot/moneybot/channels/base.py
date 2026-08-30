"""Channel contract: deliver a string to one person."""

from __future__ import annotations

from typing import Protocol


class Channel(Protocol):
    name: str

    def send(self, to: str, text: str) -> bool:
        """Return True only if the message actually went out."""
        ...
