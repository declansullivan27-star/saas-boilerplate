"""moneybot — an SMS-first money bot for 1099 athlete income.

Design rule that runs through every module: the LLM extracts and explains,
code calculates. No model output ever decides a dollar figure that lands in
the ledger without passing through :mod:`moneybot.guardrails`.
"""

__version__ = "1.0.0"
