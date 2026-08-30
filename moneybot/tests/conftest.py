import os
import sys
from datetime import date

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from moneybot import db  # noqa: E402
from moneybot.config import Config  # noqa: E402
from moneybot.router import Router  # noqa: E402

TODAY = date(2026, 8, 30)


@pytest.fixture
def conn():
    connection = db.connect(":memory:")
    db.init(connection)
    yield connection
    connection.close()


@pytest.fixture
def config(tmp_path):
    return Config(
        db_path=str(tmp_path / "test.db"),
        media_dir=str(tmp_path / "media"),
        anthropic_api_key="",
        twilio_account_sid="",
        twilio_auth_token="",
        allowed_senders=(),
        validate_twilio_signature=False,
        public_base_url="",
    )


@pytest.fixture
def bot(config):
    router = Router(config)

    def say(text, on=TODAY, party="+15550001111", media=None):
        from moneybot.router import Inbound

        return router.handle(
            Inbound(channel="test", party=party, text=text, media=media or [], today=on)
        )

    say.router = router
    return say
