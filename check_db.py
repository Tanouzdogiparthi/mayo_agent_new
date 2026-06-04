import sqlite3
import os

db_path = os.path.join(".adk", "session.db")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("\n--- ADK DATABASE SCHEMA ---")
    # Fetch all table names
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = c.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        # Fetch columns for each table
        c.execute(f"PRAGMA table_info({table_name});")
        columns = c.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
            
    conn.close()
else:
    print("Database file not found.")