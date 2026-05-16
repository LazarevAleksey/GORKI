# migrate_rtu.py
import sqlite3
import os

DB_PATH = "retarders_complete.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Проверяем, существует ли колонка status
    cursor.execute("PRAGMA table_info(devices)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Добавляем колонку status, если её нет
    if 'status' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'in_rtu'")
        print("✅ Добавлена колонка status")
    else:
        print("ℹ️ Колонка status уже существует")
    
    # Добавляем колонку rtu_batch_id, если её нет
    if 'rtu_batch_id' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN rtu_batch_id INTEGER")
        print("✅ Добавлена колонка rtu_batch_id")
    else:
        print("ℹ️ Колонка rtu_batch_id уже существует")
    
    # Добавляем колонку install_date, если её нет
    if 'install_date' not in columns:
        cursor.execute("ALTER TABLE devices ADD COLUMN install_date DATE")
        print("✅ Добавлена колонка install_date")
    else:
        print("ℹ️ Колонка install_date уже существует")
    
    # Создаём таблицы, если их нет
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rtu_batches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            batch_number TEXT NOT NULL UNIQUE,
            received_date DATE NOT NULL,
            supplier TEXT,
            invoice_number TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER
        )
    """)
    print("✅ Таблица rtu_batches создана/проверена")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS repair_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            repair_type TEXT NOT NULL,
            reason TEXT,
            defects TEXT,
            received_date DATE NOT NULL,
            completed_date DATE,
            contractor TEXT,
            result TEXT,
            act_number TEXT,
            cost REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    print("✅ Таблица repair_orders создана/проверена")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS replaced_parts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_order_id INTEGER NOT NULL,
            part_type TEXT NOT NULL,
            old_serial_number TEXT,
            new_serial_number TEXT,
            new_manufacturer TEXT,
            note TEXT,
            FOREIGN KEY (repair_order_id) REFERENCES repair_orders(id)
        )
    """)
    print("✅ Таблица replaced_parts создана/проверена")
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS device_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id INTEGER NOT NULL,
            from_location_type TEXT,
            from_location_id INTEGER,
            to_location_type TEXT,
            to_location_id INTEGER,
            movement_type TEXT NOT NULL,
            movement_date DATE NOT NULL,
            act_number TEXT,
            responsible TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (device_id) REFERENCES devices(id)
        )
    """)
    print("✅ Таблица device_movements создана/проверена")
    
    # Обновляем существующие устройства
    # Устройства на горке (с park_id) -> статус active
    cursor.execute("""
        UPDATE devices 
        SET status = 'active' 
        WHERE park_id IS NOT NULL AND (status IS NULL OR status = '')
    """)
    print(f"   Обновлено active: {cursor.rowcount}")
    
    # Остальные устройства -> в РТУ
    cursor.execute("""
        UPDATE devices 
        SET status = 'in_rtu' 
        WHERE park_id IS NULL AND (status IS NULL OR status = '')
    """)
    print(f"   Обновлено in_rtu: {cursor.rowcount}")
    
    conn.commit()
    
    # Проверка
    cursor.execute("SELECT status, COUNT(*) FROM devices GROUP BY status")
    print("\n📊 Статусы устройств после миграции:")
    for row in cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")
    
    # Проверка создания таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 Таблицы в БД: {', '.join(tables)}")
    
    conn.close()
    print("\n✅ Миграция выполнена успешно!")

if __name__ == "__main__":
    migrate()