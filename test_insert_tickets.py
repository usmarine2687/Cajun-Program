import sqlite3, os

db = os.path.join(os.path.dirname(__file__), 'Cajun_Data.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
# ensure at least one customer and boat
cur.execute('SELECT customer_id FROM Customers LIMIT 1')
if not cur.fetchone():
    cur.execute("INSERT INTO Customers(name) VALUES('FilterUser')")
    conn.commit()
cur.execute('SELECT boat_id FROM Boats LIMIT 1')
if not cur.fetchone():
    cur.execute("INSERT INTO Boats(customer_id, make, model) VALUES(1, 'FilterMake','FilterModel')")
    conn.commit()
cur.execute('INSERT INTO Tickets(customer_id, boat_id, description, status, date_closed) VALUES (?, ?, ?, ?, ?)', (1,1,'Open ticket','Open', None))
cur.execute('INSERT INTO Tickets(customer_id, boat_id, description, status, date_closed) VALUES (?, ?, ?, ?, ?)', (1,1,'In progress ticket','In Progress', None))
cur.execute('INSERT INTO Tickets(customer_id, boat_id, description, status, date_closed) VALUES (?, ?, ?, ?, ?)', (1,1,'Closed ticket','Closed','2025-01-01'))
conn.commit()
print('Inserted sample tickets')
cur.execute('SELECT ticket_id, status, date_opened, date_closed FROM Tickets')
print(cur.fetchall())
conn.close()