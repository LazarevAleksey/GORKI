# update_devices_table.py
import sqlite3

DB_PATH = "retarders_complete.db"

def update():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Добавляем новые колонки
    cursor.execute("PRAGMA table_info(devices)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'manufacturer' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN manufacturer TEXT")
        print("✅ Добавлена колонка manufacturer")
    
    if 'manufacture_date' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN manufacture_date DATE")
        print("✅ Добавлена колонка manufacture_date")
    
    if 'passport_data' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN passport_data TEXT")
        print("✅ Добавлена колонка passport_data (JSON)")
    
    conn.commit()
    conn.close()
    print("\n✅ Таблица devices обновлена!")

if __name__ == "__main__":
    update()