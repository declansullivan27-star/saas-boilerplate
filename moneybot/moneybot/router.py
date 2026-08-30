"""Channel-agnostic dispatch: one inbound message in, one reply out.

Every channel (SMS, Telegram, the CLI) hands the router the same
:class:`Inbound` and gets back a string. Nothing here knows about Twilio or
Telegram, and nothing here talks to a model except through :mod:`moneybot.llm`
with :mod:`moneybot.guardrails` on the way out.
"""

from __future__ import annotations

import hashlib
import logging
import os
import secrets
import sqlite3
from dataclasses import dataclass, field
from datetime import date

from . import advice, db, export_csv, guardrails, ledger, reply as fmt_reply, taxes
from .allocator import validate_ratios
from .config import BUCKET_ORDER, Config
from .llm import LLM
from .money import MoneyError, fmt
from .parser import parse

log = logging.getLogger("moneybot.router")

IMAGE_TYPES = ("image/jpeg", "image/png", "image/webp", "image/gif", "image/heic")
PDF_TYPES = ("application/pdf",)


@dataclass
class Media:
    data: bytes
    media_type: str
    filename: str | None = None

    @property
    def is_image(self) -> bool:
        return self.media_type.split(";")[0].strip().lower() in IMAGE_TYPES

    @property
    def is_pdf(self) -> bool:
        return self.media_type.split(";")[0].strip().lower() in PDF_TYPES


@dataclass
class Inbound:
    channel: str
    party: str
    text: str = ""
    media: list[Media] = field(default_factory=list)
    today: date | None = None


class Router:
    def __init__(self, config: Config | None = None, llm: LLM | None = None):
        self.config = config or Config()
        self.llm = llm if llm is not None else LLM(self.config)

    # --- plumbing ---------------------------------------------------------

    def connect(self) -> sqlite3.Connection:
        conn = db.connect(self.config.db_path)
        db.init(conn, self.config.ratios)
        return conn

    def _authorized(self, conn: sqlite3.Connection, party: str) -> bool:
        if self.config.allowed_senders:
            return party in self.config.allowed_senders
        owner = db.get_setting(conn, "owner")
        if owner is None:
            db.set_setting(conn, "owner", party)
            return True
        return owner == party

    def _home_state(self, conn: sqlite3.Connection) -> str:
        return db.get_setting(conn, "home_state", self.config.home_state) or self.config.home_state

    def _save_media(self, media: Media) -> str | None:
        try:
            os.makedirs(self.config.media_dir, exist_ok=True)
            digest = hashlib.sha256(media.data).hexdigest()[:20]
            suffix = {"image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(
                media.media_type.split(";")[0].strip().lower(), ".jpg"
            )
            path = os.path.join(self.config.media_dir, digest + suffix)
            with open(path, "wb") as handle:
                handle.write(media.data)
            return path
        except OSError as exc:
            log.warning("could not store media: %s", exc)
            return None

    # --- entry point ------------------------------------------------------

    def handle(self, inbound: Inbound) -> str:
        conn = self.connect()
        try:
            db.log_message(conn, "in", inbound.channel, inbound.party, inbound.text)
            if not self._authorized(conn, inbound.party):
                out = "This bot is set up for one person and you're not them."
            else:
                out = self._dispatch(conn, inbound)
            out = fmt_reply.clip(out)
            db.log_message(conn, "out", inbound.channel, inbound.party, out)
            return out
        finally:
            conn.close()

    def _dispatch(self, conn: sqlite3.Connection, inbound: Inbound) -> str:
        today = inbound.today or date.today()
        text = (inbound.text or "").strip()

        refusal = guardrails.check_inbound(text)
        if refusal:
            return refusal

        images = [m for m in inbound.media if m.is_image]
        pdfs = [m for m in inbound.media if m.is_pdf]
        if pdfs:
            return self._handle_deal(conn, text, pdfs[0])
        if images:
            return self._handle_receipt(conn, text, images[0], today)

        parsed = parse(text, today=today, default_state=self._home_state(conn))
        handler = {
            "start": lambda: fmt_reply.WELCOME,
            "help": lambda: fmt_reply.HELP,
            "spend": lambda: fmt_reply.spend_reply(advice.picture(conn, today)),
            "income": lambda: self._handle_income(conn, parsed, today),
            "expense": lambda: self._handle_expense(conn, parsed, today),
            "have": lambda: self._handle_have(conn, parsed, today),
            "bill_add": lambda: self._handle_bill_add(conn, parsed, today),
            "bills": lambda: self._handle_bills(conn, parsed, today),
            "month": lambda: self._handle_month(conn, today),
            "quarter": lambda: self._handle_quarter(conn, today),
            "deductions": lambda: self._handle_deductions(conn, today),
            "export": lambda: self._handle_export(conn, today),
            "undo": lambda: self._handle_undo(conn, today),
            "move": lambda: self._handle_move(conn, parsed, today),
            "set": lambda: self._handle_set(conn, parsed),
            "recat": lambda: self._handle_recat(conn, parsed, today),
            "deal": lambda: self._handle_deal(conn, parsed.text, None),
            "unknown": lambda: fmt_reply.UNKNOWN,
        }.get(parsed.intent)
        if handler is None:
            return fmt_reply.UNKNOWN
        try:
            return handler()
        except (ValueError, MoneyError) as exc:
            return f"Couldn't do that: {exc}"

    # --- handlers ---------------------------------------------------------

    def _handle_income(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        payment = ledger.record_payment(
            conn,
            amount_cents=parsed.amount_cents,
            source=parsed.label or "payment",
            source_type=parsed.source_type,
            date=parsed.date or today.isoformat(),
            state_sourced=ledger.normalize_state(parsed.state, self._home_state(conn)),
            raw_text=parsed.raw,
        )
        return fmt_reply.payment_reply(payment, advice.picture(conn, today))

    def _handle_expense(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        extraction = self.llm.extract_expense(
            text=parsed.raw,
            fallback_amount_cents=parsed.amount_cents,
            fallback_vendor=parsed.label,
        )
        # The amount is whatever the deterministic parser read out of his text.
        # The model may name the vendor and the category; it may not change the number.
        amount_cents = parsed.amount_cents
        bucket = "swing" if parsed.text == "swing" else self._bucket_for(extraction.category)
        expense = ledger.record_expense(
            conn,
            vendor=extraction.vendor or parsed.label or "expense",
            amount_cents=amount_cents,
            category=extraction.category,
            date=parsed.date or today.isoformat(),
            deductible=extraction.deductible,
            reason=self._vet(conn, extraction.reason, amount_cents),
            bucket=bucket,
            state_sourced=parsed.state,
            extracted_by=extraction.extracted_by,
            raw_text=parsed.raw,
        )
        out = fmt_reply.expense_reply(expense, advice.picture(conn, today))
        if parsed.confidence == "low":
            out += "\n(Read that as money OUT. If it came in, reply UNDO then say 'got X from Y'.)"
        return out

    def _handle_receipt(self, conn: sqlite3.Connection, text: str, image: Media, today: date) -> str:
        parsed = parse(text, today=today, default_state=self._home_state(conn))
        extraction = self.llm.extract_expense(
            text=text,
            image_bytes=image.data,
            media_type=image.media_type.split(";")[0].strip().lower(),
            fallback_amount_cents=parsed.amount_cents,
            fallback_vendor=parsed.label or None,
        )
        if not extraction.amount_cents:
            return (
                "Got the photo but I couldn't read a total off it. "
                "Text me the amount and vendor, like: Marriott Dallas 214.50"
            )
        receipt_path = self._save_media(image)
        expense = ledger.record_expense(
            conn,
            vendor=extraction.vendor,
            amount_cents=extraction.amount_cents,
            category=extraction.category,
            date=extraction.date or parsed.date or today.isoformat(),
            deductible=extraction.deductible,
            reason=self._vet(conn, extraction.reason, extraction.amount_cents),
            receipt_url=receipt_path,
            bucket=self._bucket_for(extraction.category),
            state_sourced=parsed.state,
            extracted_by=extraction.extracted_by,
            raw_text=text or None,
        )
        out = fmt_reply.expense_reply(expense, advice.picture(conn, today))
        if extraction.confidence == "low":
            out += "\n(Low confidence read - check the amount.)"
        return out

    def _handle_have(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        first_time = db.get_setting(conn, "opening_balance") is None
        if parsed.already_taxed:
            ledger.record_adjustment(
                conn,
                bucket="spending",
                amount_cents=parsed.amount_cents,
                reason="cash on hand, already taxed",
                date=today.isoformat(),
            )
            payment = None
        else:
            payment = ledger.record_payment(
                conn,
                amount_cents=parsed.amount_cents,
                source="starting balance",
                source_type="other",
                date=today.isoformat(),
                state_sourced=self._home_state(conn),
                raw_text=parsed.raw,
            )
        if first_time:
            db.set_setting(conn, "opening_balance", str(parsed.amount_cents))
        out = fmt_reply.have_reply(
            payment, advice.picture(conn, today), parsed.already_taxed, parsed.amount_cents
        )
        if not first_time:
            out += "\n(Added on top of what you'd already told me. UNDO if you meant to replace it.)"
        return out

    def _handle_bill_add(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        ledger.add_commitment(
            conn,
            name=parsed.label or "bill",
            amount_cents=parsed.amount_cents,
            day_of_month=parsed.day_of_month or 1,
        )
        picture = advice.picture(conn, today)
        return fmt_reply.clip(
            f"Tracking {parsed.label} {fmt(parsed.amount_cents)} on the "
            f"{fmt_reply.ordinal(parsed.day_of_month or 1)} of each month.\n"
            f"Spendable {fmt(picture.spendable_cents)}, minus {fmt(picture.committed_cents)} of bills "
            f"in the next {picture.horizon_days} days = {fmt(picture.free_cents)} free."
        )

    def _handle_bills(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        args = [a.lower() for a in parsed.args]
        if args and args[0] in ("remove", "delete", "stop", "cancel"):
            name = " ".join(parsed.args[1:]).strip()
            if not name:
                return "Which one? BILL REMOVE rent"
            if ledger.remove_commitment(conn, name):
                return f"Stopped tracking {name}."
            return f"No bill called {name}. Text BILLS to see them."
        rows = ledger.list_commitments(conn)
        return fmt_reply.bills_reply(
            rows,
            ledger.monthly_commitments_total(conn),
            ledger.commitments_due_within(conn, today, advice.HORIZON_DAYS),
        )

    def _handle_month(self, conn: sqlite3.Connection, today: date) -> str:
        start, end = advice.month_bounds(today)
        return fmt_reply.month_reply(
            advice.picture(conn, today), ledger.deductions_between(conn, start, end), today
        )

    def _handle_quarter(self, conn: sqlite3.Connection, today: date) -> str:
        quarter = taxes.next_deadline(today)
        split = taxes.state_split_for(conn, quarter)
        return fmt_reply.quarter_reply(
            advice.picture(conn, today),
            split,
            taxes.pay_links(sorted(split)),
            quarter.days_until(today),
        )

    def _handle_deductions(self, conn: sqlite3.Connection, today: date) -> str:
        start, end = f"{today.year}-01-01", f"{today.year}-12-31"
        return fmt_reply.deductions_reply(
            ledger.category_totals(conn, start, end),
            ledger.deductions_between(conn, start, end),
            today.year,
        )

    def _handle_export(self, conn: sqlite3.Connection, today: date) -> str:
        year = today.year
        paths = export_csv.write_bundle(conn, year, self.config.media_dir)
        token = db.get_setting(conn, "export_token")
        if token is None:
            token = secrets.token_urlsafe(16)
            db.set_setting(conn, "export_token", token)
        line = export_csv.totals_line(conn, year)
        if self.config.public_base_url:
            base = self.config.public_base_url.rstrip("/")
            return fmt_reply.clip(
                f"{line}\nSend your EA these:\n"
                f"{base}/export/{token}/summary-{year}.csv\n"
                f"{base}/export/{token}/expenses-{year}.csv\n"
                f"{base}/export/{token}/payments-{year}.csv",
                limit=700,
            )
        return fmt_reply.clip(f"{line}\nWritten to: " + ", ".join(os.path.basename(p) for p in paths))

    def _handle_undo(self, conn: sqlite3.Connection, today: date) -> str:
        removed = ledger.undo_last(conn)
        if not removed:
            return "Nothing to undo."
        kind, _, rest = removed.partition(":")
        _, _, tail = rest.partition(":")
        label, _, cents = tail.rpartition(":")
        picture = advice.picture(conn, today)
        return fmt_reply.clip(
            f"Removed that {kind}: {label} {fmt(int(cents))}.\n"
            f"Spendable back to {fmt(picture.spendable_cents)}."
        )

    def _handle_move(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        buckets = [a.lower() for a in parsed.args if a.lower() in BUCKET_ORDER]
        if parsed.amount_cents is None or len(buckets) < 2:
            return "Say it like: MOVE 200 swing to spending"
        src, dst = buckets[0], buckets[1]
        ledger.move_between_buckets(
            conn, src=src, dst=dst, amount_cents=parsed.amount_cents, reason="manual move"
        )
        picture = advice.picture(conn, today)
        return fmt_reply.clip(
            f"Moved {fmt(parsed.amount_cents)} from {src} to {dst}. This is bookkeeping only - "
            f"move the actual money yourself.\n"
            f"Spendable {fmt(picture.spendable_cents)}. Swing {fmt(picture.swing_cents)}."
        )

    def _handle_set(self, conn: sqlite3.Connection, parsed) -> str:
        args = parsed.args
        if len(args) < 2:
            rows = conn.execute("SELECT name, target_pct FROM buckets ORDER BY sort_order").fetchall()
            current = ", ".join(f"{r['name']} {r['target_pct'] * 100:.0f}%" for r in rows if r["name"] != "spending")
            return fmt_reply.clip(
                f"Right now: {current}, the rest is yours.\n"
                f"Home state: {self._home_state(conn)}.\n"
                "Change one: SET savings 20 | SET reserve 35 | SET state KS"
            )
        key, value = args[0].lower(), args[1]
        if key in ("state", "home", "home_state"):
            state = value.upper()[:2]
            db.set_setting(conn, "home_state", state)
            return f"Home state set to {state}. New payments default there unless you say otherwise."
        if key in ("reserve", "tax", "savings", "swing"):
            bucket = {"tax": "reserve"}.get(key, key)
            try:
                pct = float(value.strip("%")) / 100
            except ValueError:
                return "Give me a number, like: SET savings 20"
            ratios = {
                r["name"]: float(r["target_pct"])
                for r in conn.execute("SELECT name, target_pct FROM buckets").fetchall()
            }
            ratios[bucket] = pct
            ratios["spending"] = 0.0
            validate_ratios(ratios)
            conn.execute("UPDATE buckets SET target_pct = ? WHERE name = ?", (pct, bucket))
            conn.commit()
            leftover = 1.0 - sum(v for k, v in ratios.items() if k != "spending")
            return fmt_reply.clip(
                f"{bucket} is now {pct * 100:.0f}% of every payment. "
                f"That leaves {leftover * 100:.0f}% spendable.\n"
                "Applies to money that comes in from here on."
            )
        return "I can set: reserve, savings, swing, state."

    def _handle_recat(self, conn: sqlite3.Connection, parsed, today: date) -> str:
        category = parsed.text.strip()
        if not category:
            return "Say it like: CAT Travel"
        row = conn.execute("SELECT * FROM expenses ORDER BY id DESC LIMIT 1").fetchone()
        if row is None:
            return "Nothing logged yet."
        deductible = 0 if category.lower().startswith("personal") else 1
        conn.execute(
            "UPDATE expenses SET category = ?, deductible = ?, extracted_by = 'manual' WHERE id = ?",
            (category, deductible, row["id"]),
        )
        conn.commit()
        return fmt_reply.clip(
            f"{row['vendor']} {fmt(row['amount_cents'], cents_always=True)} is now {category}"
            f"{' (deductible)' if deductible else ' (not deductible)'}."
        )

    # --- deal screening ---------------------------------------------------

    def _handle_deal(self, conn: sqlite3.Connection, text: str, pdf: Media | None) -> str:
        contract = (text or "").strip()
        if pdf is not None:
            extracted = _pdf_text(pdf.data)
            if extracted:
                contract = extracted
            elif not contract:
                return (
                    "Got the PDF but couldn't read text out of it (it may be a scan). "
                    "Paste the terms as text and I'll screen them."
                )
        if len(contract) < 200:
            return fmt_reply.clip(
                "Forward me the contract PDF, or paste the whole thing as text, and I'll pull out "
                "the term, the exclusivity, what happens to your NIL rights after it ends, the "
                "auto-renewal, and the fee. I won't tell you whether to sign it."
            )
        screen = self.llm.screen_deal(contract)
        if screen is None:
            return (
                "Couldn't screen that one right now. Don't sign anything today - "
                "send it to a lawyer who does NIL work."
            )
        pdf_path = self._save_media(pdf) if pdf is not None else None
        import json as _json

        conn.execute(
            "INSERT INTO deals (counterparty, term, fee_pct, deal_type, flags, pdf_url, screen_json) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                screen.get("counterparty"),
                screen.get("term"),
                screen.get("agent_fee_pct"),
                screen.get("deal_type"),
                "; ".join(screen.get("flags") or []),
                pdf_path,
                _json.dumps(screen),
            ),
        )
        conn.commit()
        return _format_deal(screen)

    @staticmethod
    def _bucket_for(category: str) -> str:
        """A payment to the IRS draws down the reserve, not his spending money."""
        return "reserve" if (category or "").lower().startswith("taxes and licenses") else "spending"

    # --- guardrail helper --------------------------------------------------

    def _vet(self, conn: sqlite3.Connection, model_text: str, *extra_allowed: int) -> str:
        allowed = ledger.all_ledger_amounts(conn) | {c for c in extra_allowed if c}
        vetted, violations = guardrails.vet_llm_text(model_text or "", allowed, fallback="")
        if violations:
            log.warning("dropped model text: %s", violations)
        return vetted


def _pdf_text(data: bytes) -> str:
    try:
        import io

        from pypdf import PdfReader
    except ImportError:
        log.warning("pypdf not installed; cannot read PDF contracts")
        return ""
    try:
        reader = PdfReader(io.BytesIO(data))
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()
    except Exception as exc:
        log.warning("could not read PDF: %s", exc)
        return ""


def _format_deal(screen: dict) -> str:
    """Render the screen. The fee benchmark is computed here, in code -
    the model is never asked whether a number is fair."""
    from .config import FEE_BENCHMARKS

    lines = []
    who = screen.get("counterparty") or "This deal"
    lines.append(f"{who} - what's actually in it:")
    for label, key in (
        ("Term", "term"),
        ("Exclusivity", "exclusivity"),
        ("NIL rights after it ends", "nil_rights_after_term"),
        ("Auto-renewal", "auto_renewal"),
    ):
        value = screen.get(key)
        lines.append(f"- {label}: {value if value else 'not stated'}")

    fee = screen.get("agent_fee_pct")
    deal_type = (screen.get("deal_type") or "other").lower()
    if fee is not None:
        low, high = FEE_BENCHMARKS.get(
            "collective" if deal_type == "collective" else "brand", (0.03, 0.20)
        )
        band = f"{low * 100:.0f}-{high * 100:.0f}%"
        verdict = "above" if fee / 100 > high else ("in" if fee / 100 >= low else "below")
        kind = "collective money" if deal_type == "collective" else "brand deals"
        lines.append(f"- Fee: {fee:.0f}%. Typical for {kind} is {band}. This is {verdict} that range.")
    else:
        lines.append("- Fee: not stated in what you sent me. Ask before anything is signed.")

    for flag in (screen.get("flags") or [])[:3]:
        lines.append(f"! {flag}")

    lines.append("")
    lines.append("Four questions before you sign:")
    for i, question in enumerate((screen.get("questions") or [])[:4], 1):
        lines.append(f"{i}. {question}")
    lines.append("")
    lines.append("I'm not telling you this deal is fine. Have a lawyer read it.")
    return fmt_reply.clip("\n".join(lines), limit=1400)
