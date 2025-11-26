import os
import sqlite3

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'Cajun_Data.db')

def insert_test_boat(make='TestMake', model='TestModel', year=2020):
    db = get_db_path()
    print('Using DB:', db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # find any customer to attach to
    cur.execute('SELECT customer_id FROM Customers ORDER BY customer_id LIMIT 1')
    row = cur.fetchone()
    if not row:
        print('No customers found — add a customer first')
        conn.close()
        return

    customer_id = row[0]
    cur.execute('INSERT INTO Boats (customer_id, make, model, year) VALUES (?, ?, ?, ?)', (customer_id, make, model, year))
    conn.commit()
    last_id = cur.lastrowid
    print('Inserted boat id:', last_id)

    cur.execute('SELECT * FROM Boats WHERE boat_id = ?', (last_id,))
    print('Inserted row:', cur.fetchone())
    conn.close()

if __name__ == '__main__':
    insert_test_boat()
