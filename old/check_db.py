import sqlite3

DB_PATH = "retarders.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Все таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("📋 Таблицы в БД:")
for table in tables:
    print(f"   - {table[0]}")

# Структура retarders
cursor.execute("PRAGMA table_info(retarders)")
columns = cursor.fetchall()
print("\n📋 Колонки в таблице retarders:")
for col in columns:
    print(f"   - {col[1]} ({col[2]})")

# Количество записей
cursor.execute("SELECT COUNT(*) FROM retarders")
count = cursor.fetchone()[0]
print(f"\n📊 Записей в retarders: {count}")

# Пример данных
cursor.execute("SELECT id, model, inv_number, park_id FROM retarders LIMIT 3")
rows = cursor.fetchall()
print("\n📋 Пример данных:")
for row in rows:
    print(f"   ID: {row[0]}, Модель: {row[1]}, Инв.№: {row[2]}, park_id: {row[3]}")

# Таблица parks
cursor.execute("SELECT * FROM parks")
parks = cursor.fetchall()
print(f"\n📋 Парки (горки):")
for park in parks:
    print(f"   ID: {park[0]}, Название: {park[1]}")

conn.close()