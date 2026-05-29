import sqlite3
import os
from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Stores the overarching compliance event (the "freeze" action)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS compliance_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_file TEXT,
            email_subject TEXT,
            email_date TEXT,
            justification TEXT,
            funds TEXT,
            report_path TEXT,
            frozen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Stores the specific trade IDs that have been frozen, linked to the event
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frozen_trades (
            trade_id TEXT PRIMARY KEY,
            event_id INTEGER,
            FOREIGN KEY(event_id) REFERENCES compliance_events(id)
        )
    ''')

    conn.commit()
    conn.close()

def get_frozen_trade_ids():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT trade_id FROM frozen_trades")
    records = cursor.fetchall()
    conn.close()
    return [r[0] for r in records]

def get_frozen_events():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, email_subject, email_date, funds, report_path, frozen_at
        FROM compliance_events
        ORDER BY frozen_at DESC
    ''')
    records = cursor.fetchall()
    conn.close()
    return records

def get_trades_for_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT trade_id FROM frozen_trades WHERE event_id = ?", (event_id,))
    records = cursor.fetchall()
    conn.close()
    return [r[0] for r in records]

def freeze_event(email_file, email_subject, email_date, justification, funds, report_path, trade_ids):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Insert event
    cursor.execute('''
        INSERT INTO compliance_events (email_file, email_subject, email_date, justification, funds, report_path)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (email_file, email_subject, email_date, justification, ", ".join(funds), report_path))

    event_id = cursor.lastrowid

    # Insert trades
    for t_id in trade_ids:
        cursor.execute("INSERT INTO frozen_trades (trade_id, event_id) VALUES (?, ?)", (str(t_id), event_id))

    conn.commit()
    conn.close()
    return event_id

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
