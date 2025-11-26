import sqlite3
import os

# Set working directory explicitly (optional but helpful)
os.chdir("C:/Cajun Program")

# Connect to the SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect("Cajun_Data.db")
cursor = conn.cursor()

# Load and execute schema.sql to create tables
with open("schema.sql", "r") as f:
    schema = f.read()
    cursor.executescript(schema)

conn.commit()


cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:", tables)

conn.close()

print("Database initialized successfully.")
