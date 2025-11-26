import os
import sqlite3

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(base_dir), "Cajun_Data.db")

def ensure_engine_columns(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(Engines)")
    cols = {r[1] for r in cur.fetchall()}
    need = []
    if 'type' not in cols:
        need.append(("type", "TEXT"))
    if 'make' not in cols:
        need.append(("make", "TEXT"))
    if 'model' not in cols:
        need.append(("model", "TEXT"))
    if 'hp' not in cols:
        need.append(("hp", "INTEGER"))
    if 'serial_number' not in cols:
        need.append(("serial_number", "TEXT"))
    for name, ctype in need:
        try:
            cur.execute(f"ALTER TABLE Engines ADD COLUMN {name} {ctype}")
        except Exception:
            pass
    conn.commit()
    conn.close()

def ensure_assignment_work_description(db_path: str):
    """Ensure TicketAssignments table has work_description column."""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(TicketAssignments)")
    cols = {r[1] for r in cur.fetchall()}
    if 'work_description' not in cols:
        try:
            cur.execute("ALTER TABLE TicketAssignments ADD COLUMN work_description TEXT")
        except Exception:
            pass
    conn.commit()
    conn.close()
