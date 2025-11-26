import os
import sqlite3

def get_db_path():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'Cajun_Data.db')

def insert_test_customer(name='Test User', phone='555-0100', email='test@example.com', address='123 Test Lane'):
    db = get_db_path()
    print('Using DB:', db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute('INSERT INTO Customers (name, phone, email, address) VALUES (?, ?, ?, ?)', (name, phone, email, address))
    conn.commit()
    last_id = cur.lastrowid
    print('Inserted customer id:', last_id)

    cur.execute('SELECT customer_id, name, phone, email, address FROM Customers WHERE customer_id = ?', (last_id,))
    row = cur.fetchone()
    print('Inserted row:', row)
    conn.close()

if __name__ == '__main__':
    insert_test_customer()
