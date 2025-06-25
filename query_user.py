import sqlite3

conn = sqlite3.connect('instance/site.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM user WHERE email='belloumi.karim.professional@gmail.com'")
rows = cursor.fetchall()
for row in rows:
    print(row)
conn.close()
