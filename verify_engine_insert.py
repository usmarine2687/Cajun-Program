import os
import sqlite3

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'Cajun_Data.db')

def insert_test_engine(type_val='Outboard', make='Yamaha', model='V6', hp=200, serial='SN-12345'):
    db = get_db_path()
    print('Using DB:', db)
    # ensure DB has expected engine columns (best-effort)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(Engines)")
    cols = {r[1] for r in cur.fetchall()}
    to_add = []
    if 'make' not in cols:
        to_add.append(("make", "TEXT"))
    if 'model' not in cols:
        to_add.append(("model", "TEXT"))
    if 'hp' not in cols:
        to_add.append(("hp", "INTEGER"))
    if 'serial_number' not in cols:
        to_add.append(("serial_number", "TEXT"))
    for name, ctype in to_add:
        try:
            cur.execute(f"ALTER TABLE Engines ADD COLUMN {name} {ctype}")
        except Exception:
            pass
    conn.commit()
    # reopen to ensure any schema updates applied
    conn.close()
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # find any boat to attach to
    cur.execute('SELECT boat_id FROM Boats ORDER BY boat_id LIMIT 1')
    row = cur.fetchone()
    if not row:
        print('No boats found — add a boat first')
        conn.close()
        return

    boat_id = row[0]
    cur.execute('INSERT INTO Engines (boat_id, type, make, model, hp, serial_number) VALUES (?, ?, ?, ?, ?, ?)',
                (boat_id, type_val, make, model, hp, serial))
    conn.commit()
    last_id = cur.lastrowid
    print('Inserted engine id:', last_id)

    cur.execute('SELECT * FROM Engines WHERE engine_id = ?', (last_id,))
    print('Inserted row:', cur.fetchone())
    conn.close()

if __name__ == '__main__':
    insert_test_engine()
