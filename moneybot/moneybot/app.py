"""Flask app: the SMS webhook, the Telegram webhook, the CSV handoff, and the
cron endpoint that fires the nags.

Deliberately small. All the thinking is in the router.
"""

from __future__ import annotations

import hmac
import logging
import os
from datetime import date

from flask import Flask, Response, abort, request

from . import db, nag
from .channels.telegram import Telegram
from .channels.twilio_sms import TwilioSMS, twiml
from .config import Config
from .router import Inbound, Router

log = logging.getLogger("moneybot.app")


def create_app(config: Config | None = None) -> Flask:
    config = config or Config()
    app = Flask(__name__)
    app.config["MONEYBOT"] = config
    router = Router(config)
    sms = TwilioSMS(config)
    telegram = Telegram(config)

    def _webhook_url() -> str:
        """The URL Twilio signed. Behind a proxy, request.url can come back as
        http:// even though Twilio signed https://, which fails the check."""
        if config.public_base_url:
            return config.public_base_url.rstrip("/") + request.path
        return request.url

    @app.get("/healthz")
    def healthz() -> Response:
        return Response("ok", mimetype="text/plain")

    @app.post("/sms")
    def inbound_sms() -> Response:
        form = request.form.to_dict()
        if config.validate_twilio_signature:
            from .channels.twilio_sms import validate_signature

            if not validate_signature(
                config.twilio_auth_token,
                _webhook_url(),
                form,
                request.headers.get("X-Twilio-Signature", ""),
            ):
                log.warning("rejected an SMS webhook with a bad signature")
                abort(403)
        media = sms.media_from_form(form) if form.get("NumMedia", "0") not in ("", "0") else []
        inbound = Inbound(
            channel="sms",
            party=form.get("From", ""),
            text=form.get("Body", "") or "",
            media=media,
        )
        return Response(twiml(router.handle(inbound)), mimetype="application/xml")

    @app.post("/telegram/<secret>")
    def inbound_telegram(secret: str) -> Response:
        expected = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
        if not expected or not hmac.compare_digest(secret, expected):
            abort(403)
        inbound = telegram.to_inbound(request.get_json(silent=True) or {})
        if inbound is None:
            return Response("ignored", mimetype="text/plain")
        telegram.send(inbound.party, router.handle(inbound))
        return Response("ok", mimetype="text/plain")

    @app.get("/export/<token>/<path:name>")
    def export_file(token: str, name: str) -> Response:
        conn = router.connect()
        try:
            expected = db.get_setting(conn, "export_token")
        finally:
            conn.close()
        if not expected or not hmac.compare_digest(token, expected):
            abort(403)
        if "/" in name or ".." in name or not name.endswith(".csv"):
            abort(404)
        path = os.path.join(config.media_dir, name)
        if not os.path.exists(path):
            abort(404)
        with open(path, encoding="utf-8") as handle:
            body = handle.read()
        return Response(
            body,
            mimetype="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{name}"'},
        )

    @app.post("/cron/nag")
    def cron_nag() -> Response:
        expected = os.environ.get("MONEYBOT_CRON_TOKEN", "")
        supplied = request.headers.get("X-Cron-Token", "") or request.args.get("token", "")
        if not expected or not hmac.compare_digest(supplied, expected):
            abort(403)
        owner_channel = os.environ.get("MONEYBOT_NAG_CHANNEL", "sms")
        conn = router.connect()
        try:
            owner = db.get_setting(conn, "owner")
        finally:
            conn.close()
        if not owner:
            return Response("no owner yet", mimetype="text/plain")

        def send(text: str) -> bool:
            if owner_channel == "telegram":
                return telegram.send(owner, text)
            return sms.send(owner, text)

        sent = nag.run(config, send, date.today())
        return Response(f"sent {len(sent)}", mimetype="text/plain")

    return app


app = create_app()

if __name__ == "__main__":  # pragma: no cover
    logging.basicConfig(level=logging.INFO)
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
