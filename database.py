import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

columns = cursor.execute(
    "PRAGMA table_info(farmers)"
).fetchall()

print("Farmers table columns:")

for column in columns:
    print(column)

conn.close()