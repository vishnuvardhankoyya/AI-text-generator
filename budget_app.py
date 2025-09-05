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

    def parse_sms(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an SMS message.

        Implement regex or ML-based parsing here to pull the date,
        description, and amount from the message text.
        """

        return None

    def parse_email(self, message: str) -> Optional[Transaction]:
        """Extract transaction info from an email message."""

        return None


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

