"""Command line: talk to the bot without a phone, run the nags, dump the CSVs.

    python -m moneybot.cli chat
    python -m moneybot.cli send "got 10000 from the collective"
    python -m moneybot.cli nag --date 2026-09-08 --dry-run
    python -m moneybot.cli export --year 2026
    python -m moneybot.cli poll          # Telegram long-poll
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import date

from . import db, export_csv, nag as nag_module
from .config import Config
from .router import Inbound, Router

PARTY = "cli"


def _router(args) -> Router:
    config = Config()
    if args.db:
        config.db_path = args.db
    return Router(config)


def _party(router: Router) -> str:
    """The CLI speaks as the owner.

    The ledger belongs to one person; the terminal is the operator's door into
    it, not a second user. The webhook still checks the real sender.
    """
    conn = router.connect()
    try:
        return db.get_setting(conn, "owner") or PARTY
    finally:
        conn.close()


def cmd_chat(args) -> int:
    router = _router(args)
    party = _party(router)
    print("moneybot. Ctrl-D to quit. Type HELP for commands.\n")
    print(router.handle(Inbound(channel="cli", party=party, text="start")))
    while True:
        try:
            line = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue
        print("\n" + router.handle(Inbound(channel="cli", party=party, text=line)))


def cmd_send(args) -> int:
    router = _router(args)
    on = date.fromisoformat(args.date) if args.date else None
    print(
        router.handle(
            Inbound(channel="cli", party=_party(router), text=" ".join(args.message), today=on)
        )
    )
    return 0


def cmd_nag(args) -> int:
    config = Config()
    if args.db:
        config.db_path = args.db
    on = date.fromisoformat(args.date) if args.date else date.today()
    if args.dry_run:
        conn = db.connect(config.db_path)
        try:
            db.init(conn, config.ratios)
            found = nag_module.due_nags(conn, on)
        finally:
            conn.close()
        for item in found:
            print(f"--- {item.kind} {item.key} ---\n{item.text}\n")
        print(f"{len(found)} nag(s) due on {on}.")
        return 0

    from .channels.telegram import Telegram
    from .channels.twilio_sms import TwilioSMS

    conn = db.connect(config.db_path)
    try:
        db.init(conn, config.ratios)
        owner = db.get_setting(conn, "owner")
    finally:
        conn.close()
    if not owner:
        print("No owner registered yet - he has to text the bot once first.", file=sys.stderr)
        return 1
    channel = Telegram(config) if args.channel == "telegram" else TwilioSMS(config)
    sent = nag_module.run(config, lambda text: channel.send(owner, text), on)
    print(f"sent {len(sent)}")
    return 0


def cmd_export(args) -> int:
    config = Config()
    if args.db:
        config.db_path = args.db
    conn = db.connect(config.db_path)
    try:
        db.init(conn, config.ratios)
        paths = export_csv.write_bundle(conn, args.year, args.out or config.media_dir)
        print(export_csv.totals_line(conn, args.year))
    finally:
        conn.close()
    for path in paths:
        print(path)
    return 0


def cmd_poll(args) -> int:
    from .channels.telegram import Telegram

    config = Config()
    if args.db:
        config.db_path = args.db
    telegram = Telegram(config)
    if not telegram.configured:
        print("TELEGRAM_BOT_TOKEN is not set.", file=sys.stderr)
        return 1
    print("Polling Telegram. Ctrl-C to stop.")
    telegram.poll_forever(Router(config))
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="moneybot")
    parser.add_argument("--db", help="path to the SQLite file (default: $MONEYBOT_DB)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("chat", help="interactive session against the real ledger").set_defaults(func=cmd_chat)

    send = sub.add_parser("send", help="send one message and print the reply")
    send.add_argument("message", nargs="+")
    send.add_argument("--date", help="pretend today is this date (YYYY-MM-DD)")
    send.set_defaults(func=cmd_send)

    nag_cmd = sub.add_parser("nag", help="fire any due nags (cron entry point)")
    nag_cmd.add_argument("--date", help="pretend today is this date (YYYY-MM-DD)")
    nag_cmd.add_argument("--dry-run", action="store_true", help="print instead of sending")
    nag_cmd.add_argument("--channel", default="sms", choices=("sms", "telegram"))
    nag_cmd.set_defaults(func=cmd_nag)

    export = sub.add_parser("export", help="write the CSV bundle for the EA")
    export.add_argument("--year", type=int, default=date.today().year)
    export.add_argument("--out", help="output directory")
    export.set_defaults(func=cmd_export)

    poll = sub.add_parser("poll", help="Telegram long-poll loop")
    poll.set_defaults(func=cmd_poll)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
