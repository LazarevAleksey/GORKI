python -c "
import sqlite3
conn = sqlite3.connect('railway_equipment.db')
cursor = conn.cursor()

# Удаляем временную таблицу, если она существует
cursor.execute('DROP TABLE IF EXISTS equipment_models_new')

# Создаём новую таблицу без height_mm
cursor.execute('''
    CREATE TABLE equipment_models_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        manufacturer TEXT,
        max_speed_kmh REAL,
        capacity_thousand_ops INTEGER,
        emoji TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (type_id) REFERENCES equipment_types(id),
        UNIQUE(type_id, name)
    )
''')

# Копируем данные
cursor.execute('''
    INSERT INTO equipment_models_new (id, type_id, name, manufacturer, max_speed_kmh, capacity_thousand_ops, emoji, created_at)
    SELECT id, type_id, name, manufacturer, max_speed_kmh, capacity_thousand_ops, emoji, created_at
    FROM equipment_models
''')

# Заменяем таблицу
cursor.execute('DROP TABLE equipment_models')
cursor.execute('ALTER TABLE equipment_models_new RENAME TO equipment_models')

conn.commit()
conn.close()
print('✅ Готово: height_mm удалена из equipment_models')
"