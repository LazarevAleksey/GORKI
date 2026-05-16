# sync_types_to_db.py
import sqlite3
import json

DB_PATH = "railway_equipment.db"
JSON_PATH = "data/equipment_types.json"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

with open(JSON_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)
    for t in data['types']:
        cursor.execute("""
            INSERT OR REPLACE INTO equipment_types (id, name, category, icon, sort_order)
            VALUES (?, ?, ?, ?, ?)
        """, (t['id'], t['name'], None, t['icon'], t['id']))

conn.commit()
conn.close()
print("✅ Типы синхронизированы из JSON в БД")