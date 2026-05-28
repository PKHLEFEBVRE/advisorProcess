import sqlite3
import os

from config import DB_PATH

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_file TEXT UNIQUE NOT NULL,
            subject TEXT,
            date_received TEXT,
            status TEXT NOT NULL DEFAULT 'Pending',
            report_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            frozen_at TIMESTAMP,
            funds TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_pending_record(email_file, subject, date_received):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO records (email_file, subject, date_received, status)
            VALUES (?, ?, ?, 'Pending')
        ''', (email_file, subject, date_received))
        conn.commit()
    except sqlite3.IntegrityError:
        pass # Already exists
    finally:
        conn.close()

def get_pending_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email_file, subject, date_received FROM records WHERE status = 'Pending'")
    records = cursor.fetchall()
    conn.close()
    return records

def get_frozen_records():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, email_file, subject, date_received, report_path, frozen_at, funds FROM records WHERE status = 'Frozen' ORDER BY frozen_at DESC")
    records = cursor.fetchall()
    conn.close()
    return records

def freeze_record(record_id, report_path, funds):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE records
        SET status = 'Frozen', report_path = ?, frozen_at = CURRENT_TIMESTAMP, funds = ?
        WHERE id = ?
    ''', (report_path, ', '.join(funds), record_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized.")
