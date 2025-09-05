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
import logging
import re
from datetime import datetime


@dataclass
class Transaction:
    """Represents a single financial transaction."""

    date: str
    description: str
    amount: float
    currency: str = "USD"
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
    currency_symbols = {"$": "USD", "€": "EUR", "£": "GBP", "₹": "INR", "¥": "JPY"}
    debit_keywords = {"debit", "debited", "withdrawn", "purchase", "spent"}
    credit_keywords = {"credit", "credited", "deposit", "received"}
    ignore_keywords = {"failed", "reversed", "reversal"}

    amount_re = re.compile(
        r"(?P<currency>[A-Z]{3}|[$€£₹¥])\s*(?P<amount>[\d,]+(?:\.\d+)?)",
        re.IGNORECASE,
    )
    date_res = [
        re.compile(r"\d{1,2}/\d{1,2}/\d{4}"),
        re.compile(r"\d{4}-\d{1,2}-\d{1,2}"),
        re.compile(r"\d{1,2}-\d{1,2}-\d{4}"),
        re.compile(r"\d{1,2} [A-Za-z]{3,9} \d{4}"),
    ]
    date_formats = [
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m-%d-%Y",
        "%d %b %Y",
        "%d %B %Y",
    ]

    def _normalize_date(self, text: str) -> str:
        for fmt in self.date_formats:
            try:
                return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return text

    def _extract_date(self, message: str) -> str:
        for regex in self.date_res:
            match = regex.search(message)
            if match:
                return self._normalize_date(match.group())
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _parse_amount(self, message: str) -> Optional[tuple[float, str]]:
        match = self.amount_re.search(message)
        if not match:
            return None
        currency = match.group("currency").upper()
        currency = self.currency_symbols.get(currency, currency)
        amount = float(match.group("amount").replace(",", ""))
        return amount, currency

    def _parse_message(self, message: str) -> Optional[Transaction]:
        lower_msg = message.lower()
        if any(key in lower_msg for key in self.ignore_keywords):
            return None

        amount_data = self._parse_amount(message)
        if not amount_data:
            return None
        amount, currency = amount_data

        sign = 1
        if any(k in lower_msg for k in self.debit_keywords):
            sign = -1
        elif any(k in lower_msg for k in self.credit_keywords):
            sign = 1

        date = self._extract_date(message)
        description = message.strip()
        return Transaction(date=date, description=description, amount=sign * amount, currency=currency)

    def parse_sms(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an SMS message."""
        return self._parse_message(message)

    def parse_email(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an email message."""
        return self._parse_message(message)


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
        self._stop_event = asyncio.Event()
        self.logger = logging.getLogger(__name__)

    async def _stream_bank(self) -> None:
        """Stream transactions from the bank and add them to the manager."""
        async for txn in self.bank.stream_transactions():
            self.manager.add_transaction(txn)
            if self._stop_event.is_set():
                break

    async def _listen_sms(self) -> None:
        """Listen for SMS messages containing transactions.

        Replace this loop with real SMS integration that receives messages
        and passes them to :meth:`handle_sms`.
        """
        while not self._stop_event.is_set():
            await asyncio.sleep(3600)

    async def _listen_email(self) -> None:
        """Listen for emails containing transactions.

        Replace this loop with real email integration that receives messages
        and passes them to :meth:`handle_email`.
        """
        while not self._stop_event.is_set():
            await asyncio.sleep(3600)

    async def start(self) -> None:
        """Run bank, SMS, and email listeners concurrently.

        The method restarts listeners if they unexpectedly fail and logs
        exceptions. Call :meth:`stop` to shut down gracefully.
        """
        while not self._stop_event.is_set():
            try:
                await asyncio.gather(
                    self._stream_bank(),
                    self._listen_sms(),
                    self._listen_email(),
                )
            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Background task crashed; restarting...")
                await asyncio.sleep(1)
            else:
                break
        self.logger.info("RealTimeBudgetApp stopped")

    async def stop(self) -> None:
        """Signal all listeners to stop."""
        self._stop_event.set()

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

