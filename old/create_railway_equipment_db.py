# create_railway_equipment_db.py
import sqlite3
import os

DB_PATH = "railway_equipment.db"

def create_database():
    """Создание базы данных из SQL скрипта"""
    
    # Удаляем старую БД, если есть
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ Старая БД удалена")
    
    # Читаем SQL скрипт
    with open('create_railway_equipment_db.sql', 'r', encoding='utf-8') as f:
        sql_script = f.read()
    
    # Выполняем скрипт
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Разделяем скрипт на отдельные statements
    statements = sql_script.split(';')
    
    for statement in statements:
        statement = statement.strip()
        if statement and not statement.startswith('--'):
            try:
                cursor.execute(statement)
            except Exception as e:
                print(f"Ошибка: {e}")
                print(f"Проблемный SQL: {statement[:100]}...")
    
    conn.commit()
    conn.close()
    
    print(f"✅ База данных создана: {DB_PATH}")
    
    # Проверяем созданные таблицы
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = cursor.fetchall()
    print(f"\n📋 Создано таблиц: {len(tables)}")
    for table in tables[:20]:  # показываем первые 20
        print(f"   - {table[0]}")
    if len(tables) > 20:
        print(f"   ... и ещё {len(tables) - 20} таблиц")
    conn.close()

if __name__ == "__main__":
    create_database()