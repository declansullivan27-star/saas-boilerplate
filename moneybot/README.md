# moneybot

Two ways into the same idea: **an app he opens on his phone** (`app/`), and an
**SMS bot** that texts him (`moneybot/`). The app is the one he'll actually use.

---

# 1. The app — "Safe to Spend"

`app/index.html` — one file, no build step, no account, no signup.

It answers one question, in one number, on one screen: **what can I spend right
now?** Everything else on the page exists to keep that number honest.

```
              SAFE TO SPEND
              $3,208.32
       $106.94 a day for the next 30 days
      after $1,285 of bills in the next 30 days

   SWING        SAVINGS         TAX
   $1,070       $1,875        $4,625
 yours, no      put away      not yours
  questions

 ● Q3 tax due Sep 15 — 16 days
   $4,625 set aside. Estimate — confirm with your EA.

 [  MONEY IN  ]  [  MONEY OUT  ]
```

## It asks before it assumes

The first thing it does is interview him, because every default in a money app
is a guess about someone nobody has met. Seven questions, one tap each:

| It asks | Because it changes |
|---|---|
| Kansas, Missouri, or both | Which state each payment is tagged to, and which payment link he gets |
| Roughly what he'll make this year | **The tax hold** — see below |
| What's in his account today, and whether tax came out of it already | Untaxed cash gets split like any other payment; a paycheck or a gift goes straight to spendable |
| What leaves every month | Seeds the bills, so day-one spendable is real |
| How big swing and savings should be | His call, not mine |
| Whether he has an accountant | If not, every tax line reads *"you need an accountant before April"* instead of *"confirm with your EA"* |

**The tax hold is the one that matters.** A flat 37% is roughly right at $150k
and absurd at $8k. Set-aside by band — self-employment tax plus a federal and
KS/MO estimate at that income, rounded up so the error runs the safe way:

| Expected 1099 income | Actual effective rate | What it holds |
|---|---|---|
| Under $5,000 | ~14% | 18% |
| $5,000 – $25,000 | 14–18% | 22% |
| $25,000 – $75,000 | 20–24% | 28% |
| $75,000 – $150,000 | 25–28% | 32% |
| Over $150,000 | 28–31% | 36% |
| No idea yet | — | 32% |

At $120k the honest number is about 28%, so the old flat 37% was quietly
locking away an extra **$11,000 a year** and labelling it "not yours."

The screen where he picks says exactly what it is: *"a set-aside rule, not a
calculation of what you owe."* The app still never calculates his tax.

Skippable, re-runnable from Setup, and never shown to a ledger that already has
money in it.

## Why it looks like a scoreboard

Because every other money app looks like a bank. He reads a stat line without
thinking about it, so the number is enormous and monospaced, the buckets are a
box score, and the labels are tracked-out caps. Nothing on the home screen is
smaller than his thumb.

## How money moves through it

Every payment is carved up **the moment it lands**, before he sees it:

| Bucket | Default | What it is |
|---|---|---|
| Tax | 37% | Federal + self-employment + state. Shown, never spendable. |
| Savings | 15% | Put away. |
| Swing | 10% | His, for anything. The app reports it and never comments on it. |
| Spendable | the rest | The headline number. |

Spendable is the remainder bucket, so the four parts always sum to the payment
exactly — no rounding drift, ever, at any amount.

**Bills come off a rolling 30 days, not the calendar month.** On the 30th, next
month's rent is two days away. A calendar-month view would call that money
spendable; this doesn't.

## Entering money

Three ways in, fastest first:

1. **Keypad.** Tap `Money in` / `Money out`, punch the amount. Cents-first, like
   an ATM — he never types a decimal point. The split previews live as he taps:
   *"Splits into $3,700 tax · $1,500 savings · $1,000 swing · $3,800 yours."*
2. **Type it.** `got 10000 from the collective in KS`, `spent 42 on gas`,
   `rent 1200 monthly`. Parsed into the form for one tap of confirmation —
   a parse never commits money on its own.
3. **Chips.** Category is guessed from what he typed and pre-selected; the
   write-off toggle flips itself to match, and he can overrule both.

## Tax

Quarterly periods with the real IRS deadlines, weekend deadlines shifted to
Monday. Each payment is tagged **KS or MO at intake**, which is what makes a
two-state return survivable — the tax tab shows the split as a bar, with the
IRS Direct Pay link and the right state link underneath.

`Tax payment` as a category draws down the reserve instead of his spending
money, so paying the IRS never looks like it made him poorer.

**The app never calculates what he owes.** It reports what he set aside, and
says `Estimate — confirm with your EA` wherever a tax figure appears. There is
no advice in it anywhere.

## April

Three CSVs, saved straight to his phone: a summary (gross income, write-offs,
income by state), every expense, every payment. Chips say `Car & gas`; the CSV
says `Car and truck expenses`, because the EA needs the real Schedule C line.

## Where the data lives

- **This device, instantly** — `localStorage`, every change, no network needed.
- **The artifact itself, a couple of seconds later** — the page publishes
  `data/ledger.json` back to itself, so the ledger survives a cleared browser
  and shows up on his laptop. The page never republishes itself, so this view
  never reloads out from under him mid-entry.
- Whichever copy was written last wins on load, so a phone that was offline
  never loses to a stale sync.
- `Back up everything to a file` in Setup, for the paranoid case.

## Run it

```bash
cd app && python3 -m http.server 8000    # then open localhost:8000
```

Published as an artifact it picks up saving and CSV export; opened as a plain
file it still works, on this device only.

On his phone: open the link, **Share → Add to Home Screen**. It opens like any
other app after that.

## What it will never do

Give tax advice. Move money. Recommend or evaluate an investment. Show a figure
it can't derive from what he entered.

---

# 2. The SMS bot

`moneybot/` — the same rules as a Python service he texts. The app can't push a
notification; this can. Worth keeping for the four quarterly nags alone.

He texts it what he has, what he gets, and what he spends. It texts back what's
his and what isn't.

```
> got 10000 from the booster collective in KS
$10,000 in from booster collective (KS).
$3,700 to tax. $1,500 to savings. $1,000 to swing. $3,800 yours.
Spendable now $3,800. $126.66/day for the next 30 days.

> rent 1200 monthly on the 1st
Tracking rent $1,200 on the 1st of each month.
Spendable $3,800, minus $1,200 of bills in the next 30 days = $2,600 free.

> Marriott Dallas 214.50 camp appearance
Logged Marriott Dallas camp appearance $214.50 - Travel, likely deductible.
Spendable now $3,585.50. $79.51/day for the next 30 days.
Wrong? Reply UNDO.
(Read that as money OUT. If it came in, reply UNDO then say 'got X from Y'.)

> ?
Spendable: $3,585.50
minus $1,200 of bills in the next 30 days
= $2,385.50 free. $79.51/day for the next 30 days.
Swing: $1,000 - yours, no questions.
Savings $1,500. Tax reserve $3,700 - not yours.
2026-Q3 due Sep 15: $3,700 set aside. Estimate - confirm with your EA.
```

There is no dashboard, and there is never going to be one. If it isn't in a
messaging thread on his phone, it doesn't exist.

## The line that makes it safe

**The LLM extracts and explains. Code calculates.**

| Job | Who does it |
|---|---|
| Splitting a payment into tax / savings / swing / spendable | `allocator.py` — integer cents, no model |
| Deciding what's spendable, per-day, what's committed | `advice.py` — subtraction over the ledger |
| Quarterly deadlines and what's set aside | `taxes.py` — a calendar and a sum |
| Reading a vendor and amount off a receipt photo | the model (`llm.py`) |
| Pulling terms out of a contract PDF | the model (`llm.py`) |
| Benchmarking an agent fee against 3–5% / 15–20% | `router.py` — code, not the model |

Enforced, not just requested:

- Every model-written sentence passes `guardrails.vet_llm_text` before it is
  sent. Any dollar figure the ledger can't confirm, and the sentence is dropped
  and replaced with copy written in code.
- When he types an amount, that amount goes in the ledger. The model may name
  the vendor and pick the category; it may not change the number
  (`test_the_model_may_not_change_the_amount_he_typed`).
- Tax advice, investment questions and "move money to my bank" are refused on
  the way *in*, before anything else runs.
- Anything touching a tax figure is labeled `Estimate - confirm with your EA.`
- Nothing in the codebase can move money. `MOVE` is bookkeeping; the reply says so.

## The buckets

Four, fixed, in this order. `spending` is the remainder bucket and absorbs
rounding, so the parts always sum to the payment exactly.

| Bucket | Default | What it is |
|---|---|---|
| `reserve` | 37% | Federal + SE + state tax. Not his. |
| `savings` | 15% | Long-term. Not spendable. |
| `swing` | 10% | His, for anything. **The bot tracks it and never comments on it.** |
| `spending` | the rest | The number he actually asks for. |

The swing bucket is why he accepts the other 90% on autopilot. It's in from day
one, not bolted on later. Change any of them by text: `SET savings 20`.

## Multi-state (the Kansas/Missouri split)

Every payment is tagged with the state it was sourced to at intake — parsed
from the message (`in KS`, `Missouri`, `lawrence`) or falling back to
`SET state`. The tax reserve, the quarterly nag and the April CSV all break out
by state, which is the whole reason a two-state return is survivable.

## What he can text

Free text, first. Commands work with or without a leading `/`.

| Text | What happens |
|---|---|
| `got 10000 from the collective` | Logs income, splits it, replies with the four numbers |
| `i have 4200 in checking` | Starting balance (add `taxed` if it's post-tax money) |
| `spent 42 on gas` · `Marriott Dallas 214.50` | Logs an expense against spendable |
| *a photo of a receipt* | Extracted, categorized, stored, logged |
| `rent 1200 monthly on the 1st` | Tracks a recurring bill |
| `swing 200 concert tickets` | Spends out of the swing bucket |
| `?` or `SPEND` | What's spendable right now, per day, after bills |
| `TAX` | Next deadline, what's set aside, state split, payment links |
| `MONTH` | This month in four lines |
| `BILLS` / `BILL REMOVE rent` | What's committed |
| `DEDUCTIONS` | Write-offs so far this year, by category |
| `EXPORT` | Three CSVs for the EA |
| `UNDO` | Removes the last thing logged |
| `CAT Travel` | Recategorizes the last expense |
| `MOVE 200 swing to spending` | Bookkeeping move between buckets |
| `SET savings 20` · `SET state KS` | Change the split or the home state |
| `DEAL` + a forwarded PDF | Contract screen (below) |

## The nags

Cron hits `/cron/nag` once a day; the bot works out what's actually due. Safe to
call twice — each nag goes out exactly once (`nag_log` unique on kind+key), and
a failed send is retried on the next tick rather than lost.

- **1st of the month:** last month in / out, deductions logged, what's spendable
  now. If no receipts were logged, it says so.
- **21 days, 7 days, and the morning of** each quarterly deadline: the amount set
  aside from that quarter's income, the state split, and the IRS Direct Pay link
  plus the KS/MO links. Weekend deadlines shift to Monday.
- If the reserve balance has dropped below what the quarter needs, it says that
  too.

## Deal screening

Forward a contract PDF (or paste the text). It returns term length, exclusivity,
NIL rights that outlive the deal, auto-renewal, the fee — and **four questions to
ask before signing**. Never "this is fine."

The fee benchmark is computed in `_format_deal`, in code:

```
- Fee: 20%. Typical for collective money is 3-5%. This is above that range.
```

On $120k of collective money that line is worth about $18k a year.

## Run it

```bash
pip install -r requirements.txt
python -m moneybot.cli chat          # talk to it in a terminal, real ledger
python -m pytest                      # 201 tests, no network
```

Try a whole month without sending a text:

```bash
python -m moneybot.cli send "got 10000 from the collective in KS" --date 2026-08-05
python -m moneybot.cli send "rent 1200 monthly on the 1st"
python -m moneybot.cli send "?"
python -m moneybot.cli nag --date 2026-09-08 --dry-run
python -m moneybot.cli export --year 2026
```

## Deploy

```bash
cp .env.example .env      # fill it in
fly launch --no-deploy && fly volumes create moneybot_data --size 1 && fly deploy
```

Railway works the same way (`railway.json` is here); point `MONEYBOT_DB` at a
mounted volume either way — the ledger must outlive a deploy.

Then:

1. **Twilio** → buy a number → Messaging → *A message comes in* → `POST https://<host>/sms`.
   Leave `MONEYBOT_VALIDATE_SIGNATURE=1` and set `MONEYBOT_BASE_URL`; the webhook
   is public and the signature check is what protects it.
2. **Cron** → daily `curl -H "X-Cron-Token: $MONEYBOT_CRON_TOKEN" https://<host>/cron/nag`
   (see `crontab.example`).
3. Have him text the bot once. The first sender is remembered as the owner and
   everyone else gets turned away — or pin it down ahead of time with
   `MONEYBOT_ALLOWED_SENDERS`.

### On the Twilio account

A2P 10DLC registration is a business-entity process and the account holder is on
the hook for the traffic. Put the Twilio account in **Kevin's** name — he's 18+,
it's his money, and it makes the sender and the person being texted the same
person. Registration takes a few days; until it clears, or if you want to skip it
entirely, run the same bot on Telegram (`TELEGRAM_BOT_TOKEN`, then
`python -m moneybot.cli poll`) — same router, same ledger, free photos.

## Layout

```
moneybot/
  money.py        integer-cent arithmetic; the only place floats are allowed
  db.py           SQLite schema. Balances are derived, never stored.
  allocator.py    the split. Deterministic. No model.
  ledger.py       writes, balances, bills, undo
  advice.py       "what can I spend right now"
  taxes.py        quarterly calendar and reserve math
  parser.py       free-text SMS -> intent. Regex first, model second.
  llm.py          receipt extraction + deal screening, with a keyword floor
  prompts.py      system prompts and JSON schemas
  guardrails.py   inbound refusals and outbound verification
  reply.py        outbound copy. ASCII-only, length-capped.
  router.py       one message in, one reply out. Channel-agnostic.
  nag.py          the cron jobs
  export_csv.py   April, in one command
  app.py          Flask: /sms, /telegram, /export, /cron/nag
  cli.py          chat, send, nag, export, poll
  channels/       twilio_sms.py, telegram.py
```

## Where the money actually comes from

Not investment returns. It's a leak-stopper:

- Recovered deductions: **$2–5k/year** on $120k of 1099 income
- Avoided penalties and a correct two-state filing
- Not overpaying an agent: **$20k+/year**
- Not signing an exclusivity clause that outlives the deal
- The savings that happen because the money left before he saw it

## What it will never do

Generate tax advice. Move money. Recommend or evaluate an investment. Tell him a
deal is fine. Send a dollar figure the ledger can't back up.
