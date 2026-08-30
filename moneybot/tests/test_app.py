import base64
import hashlib
import hmac
import os

import pytest

from moneybot.app import create_app

FROM = "+15550001111"


@pytest.fixture
def client(config):
    return create_app(config).test_client()


def _sign(token, url, params):
    payload = url + "".join(f"{key}{params[key]}" for key in sorted(params))
    return base64.b64encode(
        hmac.new(token.encode(), payload.encode(), hashlib.sha1).digest()
    ).decode()


def test_health(client):
    assert client.get("/healthz").data == b"ok"


def test_the_sms_webhook_answers_with_twiml(client):
    response = client.post("/sms", data={"From": FROM, "Body": "got 10000 from the collective", "NumMedia": "0"})
    assert response.status_code == 200
    assert response.mimetype == "application/xml"
    body = response.data.decode()
    assert "$3,700 to tax" in body
    assert body.startswith("<?xml")


def test_an_unsigned_webhook_is_rejected_when_validation_is_on(config):
    config.validate_twilio_signature = True
    config.twilio_auth_token = "secret"
    config.public_base_url = "https://bot.example.com"
    client = create_app(config).test_client()
    assert client.post("/sms", data={"From": FROM, "Body": "?", "NumMedia": "0"}).status_code == 403


def test_a_correctly_signed_webhook_is_accepted(config):
    config.validate_twilio_signature = True
    config.twilio_auth_token = "secret"
    config.public_base_url = "https://bot.example.com"
    client = create_app(config).test_client()
    form = {"From": FROM, "Body": "?", "NumMedia": "0"}
    response = client.post(
        "/sms",
        data=form,
        headers={"X-Twilio-Signature": _sign("secret", "https://bot.example.com/sms", form)},
    )
    assert response.status_code == 200


def test_the_telegram_webhook_needs_the_shared_secret(client, monkeypatch):
    monkeypatch.setenv("TELEGRAM_WEBHOOK_SECRET", "shhh")
    assert client.post("/telegram/wrong", json={}).status_code == 403


def test_the_telegram_webhook_is_closed_when_no_secret_is_set(client, monkeypatch):
    monkeypatch.delenv("TELEGRAM_WEBHOOK_SECRET", raising=False)
    assert client.post("/telegram/anything", json={}).status_code == 403


def test_the_export_route_needs_the_token(config):
    app = create_app(config)
    client = app.test_client()
    client.post("/sms", data={"From": FROM, "Body": "got 10000 from the collective", "NumMedia": "0"})
    client.post("/sms", data={"From": FROM, "Body": "export", "NumMedia": "0"})

    from moneybot import db

    conn = db.connect(config.db_path)
    token = db.get_setting(conn, "export_token")
    conn.close()

    assert client.get("/export/wrong/summary-2026.csv").status_code == 403
    year_file = [n for n in os.listdir(config.media_dir) if n.startswith("summary-")][0]
    good = client.get(f"/export/{token}/{year_file}")
    assert good.status_code == 200
    assert good.mimetype == "text/csv"
    assert b"Gross 1099 income" in good.data


def test_the_export_route_will_not_walk_the_filesystem(config):
    app = create_app(config)
    client = app.test_client()
    client.post("/sms", data={"From": FROM, "Body": "export", "NumMedia": "0"})
    from moneybot import db

    conn = db.connect(config.db_path)
    token = db.get_setting(conn, "export_token")
    conn.close()
    assert client.get(f"/export/{token}/../../etc/passwd").status_code in (403, 404)
    assert client.get(f"/export/{token}/moneybot.db").status_code == 404


def test_the_cron_endpoint_needs_its_token(client, monkeypatch):
    monkeypatch.delenv("MONEYBOT_CRON_TOKEN", raising=False)
    assert client.post("/cron/nag").status_code == 403
    monkeypatch.setenv("MONEYBOT_CRON_TOKEN", "cron-secret")
    assert client.post("/cron/nag", headers={"X-Cron-Token": "nope"}).status_code == 403
    ok = client.post("/cron/nag", headers={"X-Cron-Token": "cron-secret"})
    assert ok.status_code == 200
    assert b"no owner" in ok.data
