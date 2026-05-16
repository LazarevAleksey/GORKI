# sync_models_to_db.py
import sqlite3
import json

DB_PATH = "railway_equipment.db"
JSON_PATH = "data/retarder_models.json"


def sync_models():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Получаем ID типа "Замедлитель"
    cursor.execute("SELECT id FROM equipment_types WHERE name = 'Замедлитель'")
    row = cursor.fetchone()
    if not row:
        print("❌ Тип 'Замедлитель' не найден")
        return
    
    retarder_type_id = row[0]
    
    # Загружаем JSON
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
        models = data.get('models', [])
    
    # Проверяем существующие колонки в equipment_models
    cursor.execute("PRAGMA table_info(equipment_models)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    # Добавляем недостающие колонки
    if 'height_mm' not in existing_columns:
        cursor.execute("ALTER TABLE equipment_models ADD COLUMN height_mm INTEGER")
        print("✅ Добавлена колонка height_mm в equipment_models")
    
    if 'manufacturer' not in existing_columns:
        cursor.execute("ALTER TABLE equipment_models ADD COLUMN manufacturer TEXT")
        print("✅ Добавлена колонка manufacturer в equipment_models")
    
    if 'emoji' not in existing_columns:
        cursor.execute("ALTER TABLE equipment_models ADD COLUMN emoji TEXT")
        print("✅ Добавлена колонка emoji в equipment_models")
    
    count = 0
    for model in models:
        cursor.execute("""
            INSERT OR REPLACE INTO equipment_models 
            (id, type_id, name, height_mm, manufacturer, emoji)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            model['id'],
            retarder_type_id,
            model['name'],
            model.get('height_mm'),
            model.get('manufacturer'),
            model.get('emoji')
        ))
        count += 1
        print(f"✅ {model['name']} (высота: {model.get('height_mm')} мм) - {model.get('manufacturer')}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Синхронизировано моделей: {count}")


if __name__ == "__main__":
    sync_models()