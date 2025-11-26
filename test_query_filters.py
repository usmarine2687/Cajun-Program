import sqlite3, os

db = os.path.join(os.path.dirname(__file__), 'Cajun_Data.db')
conn = sqlite3.connect(db)
cur = conn.cursor()
print('Closed tickets:', cur.execute("SELECT ticket_id,status FROM Tickets WHERE status='Closed'").fetchall())
print('Customer Filter (FilterUser):', cur.execute("SELECT ticket_id,status FROM Tickets t JOIN Customers c ON t.customer_id=c.customer_id WHERE c.name LIKE '%FilterUser%'").fetchall())
print('Boat Filter (FilterMake):', cur.execute("SELECT ticket_id,status FROM Tickets t JOIN Boats b ON t.boat_id=b.boat_id WHERE b.make LIKE '%FilterMake%' OR b.model LIKE '%FilterMake%'").fetchall())
conn.close()
