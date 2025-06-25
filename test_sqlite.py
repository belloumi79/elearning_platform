import sqlite3
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("INSERT INTO test (name) VALUES ('hello')")
cursor.execute("SELECT * FROM test")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
