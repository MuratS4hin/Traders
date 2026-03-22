"""
Demo transaction logic with SQLite persistence.

Schema:
    transactions (
        id        INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker    TEXT    NOT NULL,
        action    TEXT    NOT NULL,  -- BUY | SELL | HOLD
        price     REAL    NOT NULL,
        quantity  INTEGER NOT NULL DEFAULT 1,
        timestamp TEXT    NOT NULL
    )
"""

import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "traders.db")


def _get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the transactions table if it does not exist."""
    with _get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker    TEXT    NOT NULL,
                action    TEXT    NOT NULL,
                price     REAL    NOT NULL,
                quantity  INTEGER NOT NULL DEFAULT 1,
                timestamp TEXT    NOT NULL
            )
            """
        )
        conn.commit()


def record_transaction(ticker: str, action: str, price: float, quantity: int = 1) -> dict:
    """
    Persist a demo transaction and return it as a dict.

    :param ticker:   Stock ticker symbol
    :param action:   "BUY", "SELL", or "HOLD"
    :param price:    Execution price
    :param quantity: Number of shares (default 1)
    :return: Saved transaction as a dict
    """
    if action not in ("BUY", "SELL", "HOLD"):
        raise ValueError(f"Invalid action '{action}'. Must be BUY, SELL, or HOLD.")

    timestamp = datetime.now(timezone.utc).isoformat()

    with _get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO transactions (ticker, action, price, quantity, timestamp) VALUES (?, ?, ?, ?, ?)",
            (ticker, action, price, quantity, timestamp),
        )
        conn.commit()
        row_id = cursor.lastrowid

    return {
        "id": row_id,
        "ticker": ticker,
        "action": action,
        "price": price,
        "quantity": quantity,
        "timestamp": timestamp,
    }


def get_all_transactions() -> list:
    """Return all transactions ordered by most recent first."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_transactions_by_ticker(ticker: str) -> list:
    """Return all transactions for a specific ticker ordered by most recent first."""
    with _get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM transactions WHERE ticker = ? ORDER BY id DESC",
            (ticker,),
        ).fetchall()
    return [dict(row) for row in rows]
