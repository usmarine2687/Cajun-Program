"""
Database initialization script.
Drops the existing database and creates fresh tables from schema.sql
"""
import sqlite3
import os

def get_db_path():
    """Return the absolute path to the database file."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(current_dir, 'Cajun_Data.db')

def get_schema_path():
    """Return the absolute path to the schema.sql file."""
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(current_dir, 'schema.sql')

def init_database():
    """Initialize the database from schema.sql"""
    db_path = get_db_path()
    schema_path = get_schema_path()
    
    # Delete existing database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Deleted existing database: {db_path}")
    
    # Read schema
    with open(schema_path, 'r') as f:
        schema_sql = f.read()
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Execute schema
    cursor.executescript(schema_sql)
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully: {db_path}")
    print("Tables created from schema.sql")

if __name__ == '__main__':
    init_database()
