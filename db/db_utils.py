import os
import sqlite3

def get_db_path():
    """Return the absolute path to the database file."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(base_dir), "Cajun_Data.db")

def _format_phone(raw_phone: str) -> str:
    """Format phone as (###)###-#### if it has 10 digits; otherwise return original stripped."""
    if not raw_phone:
        return ''
    digits = ''.join(ch for ch in str(raw_phone) if ch.isdigit())
    if len(digits) == 10:
        return f"({digits[0:3]}){digits[3:6]}-{digits[6:10]}"
    return str(raw_phone).strip()

def ensure_database_exists():
    """Ensure database exists by creating from schema if needed."""
    db_path = get_db_path()
    if not os.path.exists(db_path):
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'schema.sql')
        if os.path.exists(schema_path):
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.executescript(schema_sql)
            conn.commit()
            conn.close()
