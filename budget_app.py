"""Simple budget tracking app skeleton.

This module provides placeholder classes for connecting to a bank
aggregator, parsing SMS and email for transactions, and managing a
user's budget. The implementation details are left as exercises for the
user, but the structure gives a starting point for a full application.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import asyncio
import re


@dataclass
class Transaction:
    """Represents a single financial transaction."""

    date: str
    description: str
    amount: float
    category: Optional[str] = None


class BankConnector:
    """Placeholder for a bank aggregator connection."""

    def fetch_transactions(self) -> List[Transaction]:
        """Fetch recent transactions from the bank.

        Replace this stub with real logic using an aggregator such as
        Plaid or Salt Edge. Ensure tokens are stored securely and API
        calls are authenticated.
        """

        raise NotImplementedError("Bank integration not implemented")

    async def stream_transactions(self, poll_interval: float = 60.0):
        """Yield new transactions by periodically polling the bank.

        This simple implementation stores seen transactions in memory and
        repeatedly calls :meth:`fetch_transactions`. Real applications should
        persist transaction identifiers and use bank-provided webhooks where
        possible for lower latency updates.
        """
        seen = set()
        while True:
            for txn in self.fetch_transactions():
                key = (txn.date, txn.description, txn.amount)
                if key not in seen:
                    seen.add(key)
                    yield txn
            await asyncio.sleep(poll_interval)


class MessageParser:
    """Parses SMS or email messages for transaction data."""
    _DATE_PATTERNS = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
        r"\d{4}[/-]\d{1,2}[/-]\d{1,2}",
        r"\d{1,2}\s+[A-Za-z]{3,9}\s+\d{2,4}",
    ]

    _AMOUNT_RE = re.compile(
        r"(?P<sign>-)?(?P<currency>[A-Z]{3}|[$€£₹])?\s?"
        r"(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d+)?|\d+(?:\.\d+)?)"
        r"\s?(?P<currency_after>[A-Z]{3})?",
        re.IGNORECASE,
    )

    def _parse_message(self, message: str) -> Optional[Transaction]:
        """Common parsing logic for SMS and email bodies.

        The heuristic supports a variety of formats such as:
            'Acct 1234 debited with INR 1,234.56 at Amazon on 12-05-2023'
            'You were credited $50.23 from PAYPAL 2023/05/12'

        Messages describing failed or reversed transactions return ``None``.
        """

        lower = message.lower()
        if any(word in lower for word in [
            "failed",
            "declined",
            "reversed",
            "reversal",
            "unsuccessful",
            "cancelled",
        ]):
            return None

        amount_match = self._AMOUNT_RE.search(message)
        if not amount_match:
            return None

        amount = float(amount_match.group("amount").replace(",", ""))
        if amount_match.group("sign") == "-":
            amount = -amount

        debit_words = {
            "debited",
            "purchase",
            "spent",
            "withdrawn",
            "payment",
            "paid",
            "sent",
        }
        credit_words = {
            "credited",
            "received",
            "deposit",
            "added",
            "refunded",
        }
        if any(w in lower for w in debit_words):
            amount = -abs(amount)
        elif any(w in lower for w in credit_words):
            amount = abs(amount)

        date = "unknown"
        for pattern in self._DATE_PATTERNS:
            m = re.search(pattern, message)
            if m:
                date = m.group(0)
                break

        description = "transaction"
        for key in ("at", "from", "to"):
            m = re.search(rf"{key}\s+([A-Za-z0-9 &._-]+)", message, re.IGNORECASE)
            if m:
                description = re.split(r"\s+on\s+|,|\.|!", m.group(1))[0].strip()
                break

        return Transaction(date=date, description=description, amount=amount)

    def parse_sms(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an SMS message."""
        return self._parse_message(message)

    def parse_email(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an email message."""
        normalized = " ".join(message.split())
        return self._parse_message(normalized)


@dataclass
class BudgetManager:
    """Tracks income, expenses, and category budgets."""

    transactions: List[Transaction] = field(default_factory=list)

    def add_transaction(self, txn: Transaction) -> None:
        """Add a transaction to the ledger."""

        self.transactions.append(txn)

    def total_income(self) -> float:
        """Calculate total income."""

        return sum(t.amount for t in self.transactions if t.amount > 0)

    def total_expenses(self) -> float:
        """Calculate total expenses."""

        return sum(-t.amount for t in self.transactions if t.amount < 0)


class RealTimeBudgetApp:
    """Coordinates bank polling and message parsing for live updates."""

    def __init__(
        self,
        bank: BankConnector,
        parser: MessageParser,
        manager: BudgetManager,
    ) -> None:
        self.bank = bank
        self.parser = parser
        self.manager = manager

    async def start(self) -> None:
        """Begin streaming bank transactions into the budget manager."""
        async for txn in self.bank.stream_transactions():
            self.manager.add_transaction(txn)

    def handle_sms(self, message: str) -> None:
        """Process an incoming SMS message for transactions."""
        txn = self.parser.parse_sms(message)
        if txn:
            self.manager.add_transaction(txn)

    def handle_email(self, message: str) -> None:
        """Process an incoming email for transactions."""
        txn = self.parser.parse_email(message)
        if txn:
            self.manager.add_transaction(txn)


__all__ = [
    "Transaction",
    "BankConnector",
    "MessageParser",
    "BudgetManager",
    "RealTimeBudgetApp",
]

