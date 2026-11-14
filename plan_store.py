import json
from pathlib import Path
import sqlite3


DB_FILE = Path(__file__).resolve().parent / "data/plans.sqlite3"


def load_plan(day):
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute(
            "CREATE TABLE IF NOT EXISTS plans "
            "(day TEXT PRIMARY KEY, tasks TEXT NOT NULL, revision INTEGER NOT NULL)"
        )
        row = connection.execute(
            "SELECT tasks, revision FROM plans WHERE day = ?", (str(day),)
        ).fetchone()
    return (json.loads(row[0]), row[1]) if row else ([], 0)


def save_plan(day, tasks, revision):
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute(
            "SELECT revision FROM plans WHERE day = ?", (str(day),)
        ).fetchone()
        if (row[0] if row else 0) != revision:
            raise ValueError("This plan changed in another tab. Refresh and try again.")
        connection.execute(
            "INSERT INTO plans VALUES (?, ?, ?) ON CONFLICT(day) DO UPDATE "
            "SET tasks = excluded.tasks, revision = excluded.revision",
            (str(day), json.dumps(tasks, allow_nan=False), revision + 1),
        )
