import base64
import hashlib
import hmac

import pytest

from moneybot.channels.telegram import Telegram
from moneybot.channels.twilio_sms import TwilioSMS, twiml, validate_signature

URL = "https://bot.example.com/sms"
TOKEN = "test-auth-token"
FORM = {"From": "+15550001111", "Body": "got 10000 from the collective", "NumMedia": "0"}


def _sign(token, url, params):
    payload = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    return base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


def test_a_valid_twilio_signature_passes():
    assert validate_signature(TOKEN, URL, FORM, _sign(TOKEN, URL, FORM))


@pytest.mark.parametrize(
    "token,url,form",
    [
        ("wrong-token", URL, FORM),
        (TOKEN, "https://bot.example.com/other", FORM),
        (TOKEN, URL, {**FORM, "Body": "tampered"}),
    ],
)
def test_a_tampered_request_fails(token, url, form):
    assert not validate_signature(TOKEN, URL, FORM, _sign(token, url, form))


def test_a_missing_signature_or_token_fails():
    assert not validate_signature(TOKEN, URL, FORM, "")
    assert not validate_signature("", URL, FORM, _sign(TOKEN, URL, FORM))


def test_twiml_escapes_markup():
    body = twiml("Marriott & <b>Dallas</b>")
    assert "&amp;" in body and "&lt;b&gt;" in body
    assert "<Message>" in body


def test_twilio_refuses_to_send_when_unconfigured(config):
    assert TwilioSMS(config).configured is False
    assert TwilioSMS(config).send("+15550001111", "hi") is False


def test_telegram_reads_a_text_update(config):
    inbound = Telegram(config).to_inbound(
        {"message": {"chat": {"id": 4242}, "text": "spent 42 on gas"}}
    )
    assert inbound.channel == "telegram"
    assert inbound.party == "4242"
    assert inbound.text == "spent 42 on gas"


def test_telegram_uses_the_caption_for_a_photo(config, monkeypatch):
    telegram = Telegram(config)
    monkeypatch.setattr(telegram, "download", lambda file_id: b"jpegbytes")
    inbound = telegram.to_inbound(
        {
            "message": {
                "chat": {"id": 7},
                "caption": "camp appearance",
                "photo": [
                    {"file_id": "small", "file_size": 10},
                    {"file_id": "large", "file_size": 900},
                ],
            }
        }
    )
    assert inbound.text == "camp appearance"
    assert len(inbound.media) == 1
    assert inbound.media[0].is_image


def test_telegram_accepts_a_pdf_document(config, monkeypatch):
    telegram = Telegram(config)
    monkeypatch.setattr(telegram, "download", lambda file_id: b"%PDF-1.4")
    inbound = telegram.to_inbound(
        {
            "message": {
                "chat": {"id": 7},
                "document": {"file_id": "d", "mime_type": "application/pdf", "file_name": "nil.pdf"},
            }
        }
    )
    assert inbound.media[0].is_pdf


def test_telegram_ignores_updates_with_nothing_in_them(config):
    assert Telegram(config).to_inbound({}) is None
    assert Telegram(config).to_inbound({"message": {"chat": {"id": 1}}}) is None
