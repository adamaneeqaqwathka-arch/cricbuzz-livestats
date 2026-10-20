from utils.db_connection import get_connection

conn = get_connection()
cursor = conn.cursor()
cursor.execute("SHOW TABLES")
print(cursor.fetchall())
conn.close()