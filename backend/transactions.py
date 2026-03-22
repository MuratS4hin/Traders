"""
Demo transaction logic with PostgreSQL persistence.

The database connection is configured via the DATABASE_URL environment variable:

    DATABASE_URL=postgresql://user:password@host:5432/dbname

Schema:
    transactions (
        id        SERIAL  PRIMARY KEY,
        ticker    TEXT    NOT NULL,
        action    TEXT    NOT NULL,  -- BUY | SELL | HOLD
        price     NUMERIC NOT NULL,
        quantity  INTEGER NOT NULL DEFAULT 1,
        timestamp TEXT    NOT NULL
    )
"""

import os
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://neondb_owner:npg_CArg8f6RiuWH@ep-quiet-dust-a8yflq7j-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require",
)


def _get_connection() -> psycopg2.extensions.connection:
    """Return a new psycopg2 connection using DATABASE_URL."""
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    """Create the transactions table if it does not exist."""
    with _get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id        SERIAL  PRIMARY KEY,
                    ticker    TEXT    NOT NULL,
                    action    TEXT    NOT NULL,
                    price     NUMERIC NOT NULL,
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
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO transactions (ticker, action, price, quantity, timestamp)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
                """,
                (ticker, action, price, quantity, timestamp),
            )
            row_id = cur.fetchone()[0]
        conn.commit()

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
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM transactions ORDER BY id DESC")
            rows = cur.fetchall()
    return [dict(row) for row in rows]


def get_transactions_by_ticker(ticker: str) -> list:
    """Return all transactions for a specific ticker ordered by most recent first."""
    with _get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT * FROM transactions WHERE ticker = %s ORDER BY id DESC",
                (ticker,),
            )
            rows = cur.fetchall()
    return [dict(row) for row in rows]

