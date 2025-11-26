import os
import sqlite3


def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'Cajun_Data.db')


def insert_test_ticket(description='Test ticket', status='Open'):
    db = get_db_path()
    print('Using DB:', db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # find any customer and boat to attach to
    cur.execute('SELECT customer_id FROM Customers ORDER BY customer_id LIMIT 1')
    crow = cur.fetchone()
    cur.execute('SELECT boat_id FROM Boats ORDER BY boat_id LIMIT 1')
    brow = cur.fetchone()
    if not crow or not brow:
        print('Need at least one customer and one boat to create a ticket')
        conn.close()
        return

    cust_id = crow[0]
    boat_id = brow[0]

    cur.execute('INSERT INTO Tickets (customer_id, boat_id, description, status) VALUES (?, ?, ?, ?)', (cust_id, boat_id, description, status))
    conn.commit()
    tid = cur.lastrowid
    print('Inserted ticket id:', tid)

    cur.execute('SELECT * FROM Tickets WHERE ticket_id = ?', (tid,))
    print('Inserted row:', cur.fetchone())
    conn.close()


if __name__ == '__main__':
    insert_test_ticket()
