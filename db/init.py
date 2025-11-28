import os
import sqlite3

def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_db_path():
    return os.path.join(get_root_dir(), 'Cajun_Data.db')

def get_schema_path():
    return os.path.join(get_root_dir(), 'schema.sql')

def _table_exists(cur, name: str) -> bool:
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,))
    return cur.fetchone() is not None

def _column_exists(cur, table: str, column: str) -> bool:
    cur.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())

def initialize_database():
    """Create tables if missing and apply idempotent migrations."""
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Create schema tables if not present
    schema_path = get_schema_path()
    if os.path.exists(schema_path):
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        # Use executescript; SQLite will ignore CREATE TABLE IF NOT EXISTS if authored so.
        try:
            cur.executescript(schema_sql)
        except sqlite3.Error:
            # If schema has plain CREATE TABLE, skip errors for existing tables.
            pass

    # Migrations: add columns safely
    # Engines
    if _table_exists(cur, 'Engines'):
        if not _column_exists(cur, 'Engines', 'engine_type'):
            cur.execute("ALTER TABLE Engines ADD COLUMN engine_type TEXT")
            cur.execute("UPDATE Engines SET engine_type = type WHERE engine_type IS NULL")
        if not _column_exists(cur, 'Engines', 'outdrive'):
            cur.execute("ALTER TABLE Engines ADD COLUMN outdrive TEXT")
        if not _column_exists(cur, 'Engines', 'year'):
            cur.execute("ALTER TABLE Engines ADD COLUMN year INTEGER")

    # Mechanics
    if _table_exists(cur, 'Mechanics'):
        if not _column_exists(cur, 'Mechanics', 'phone'):
            cur.execute("ALTER TABLE Mechanics ADD COLUMN phone TEXT")
        if not _column_exists(cur, 'Mechanics', 'email'):
            cur.execute("ALTER TABLE Mechanics ADD COLUMN email TEXT")

    # Boats
    if _table_exists(cur, 'Boats'):
        for col in ('color1', 'color2', 'color3'):
            if not _column_exists(cur, 'Boats', col):
                cur.execute(f"ALTER TABLE Boats ADD COLUMN {col} TEXT")

    # Tickets
    if _table_exists(cur, 'Tickets'):
        if not _column_exists(cur, 'Tickets', 'customer_notes'):
            cur.execute("ALTER TABLE Tickets ADD COLUMN customer_notes TEXT")

    # LaborRates single-row table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS LaborRates (
            id INTEGER PRIMARY KEY,
            outboard REAL,
            inboard REAL,
            sterndrive REAL,
            pwc REAL
        )
    """)
    # Ensure a single default row exists (id=1)
    cur.execute("SELECT id FROM LaborRates WHERE id=1")
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO LaborRates (id, outboard, inboard, sterndrive, pwc) VALUES (1, ?, ?, ?, ?)",
            (100.0, 120.0, 120.0, 120.0)
        )

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()
