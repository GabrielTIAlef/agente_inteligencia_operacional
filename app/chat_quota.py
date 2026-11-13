"""Persistent global request budget for a single public demo VM.

This bounds requests, not billing. The provider project must remain on Free.
"""
from datetime import datetime
from pathlib import Path
import sqlite3
from zoneinfo import ZoneInfo

def reserve_request(path='/var/lib/aio/chat-quota.sqlite3', limit=30):
    slot = datetime.now(ZoneInfo('America/Sao_Paulo')).date().isoformat()
    with sqlite3.connect(Path(path), timeout=2) as connection:
        connection.execute('CREATE TABLE IF NOT EXISTS daily (slot TEXT PRIMARY KEY, requests INTEGER NOT NULL)')
        cursor = connection.execute('''INSERT INTO daily VALUES (?, 1)
            ON CONFLICT(slot) DO UPDATE SET requests = requests + 1
            WHERE requests < ? RETURNING requests''', (slot, limit))
        return cursor.fetchone() is not None
