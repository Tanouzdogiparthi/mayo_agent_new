import sqlite3

conn = sqlite3.connect(".adk/session.db")
c = conn.cursor()

c.execute("""
SELECT id, create_time
FROM sessions
ORDER BY create_time DESC
""")

for row in c.fetchall():
    print(row)
    print(type(row[1]))

conn.close()