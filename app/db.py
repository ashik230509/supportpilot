import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "supportpilot.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY, name TEXT, email TEXT,
    phone TEXT, preferred_language TEXT
);
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY, customer_id INTEGER, product_name TEXT,
    amount REAL, status TEXT, order_date TEXT,
    expected_delivery TEXT, delivered_date TEXT
);
CREATE TABLE IF NOT EXISTS refunds (
    id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER,
    amount REAL, reason TEXT, status TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER, order_id INTEGER,
    message TEXT, language TEXT, intent TEXT, status TEXT,
    agent_reply TEXT, escalated INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)