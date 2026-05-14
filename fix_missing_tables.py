# fix_missing_tables.py
import sqlite3

DB_PATH = "railway_equipment.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 1. Создаём таблицу equipment_types (типы оборудования)
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    icon TEXT,
    has_passport BOOLEAN DEFAULT 1,
    has_serial_number BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0
)
""")

# 2. Создаём таблицу parks (горки)
cursor.execute("""
CREATE TABLE IF NOT EXISTS parks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    station TEXT,
    class INTEGER,
    num_tracks INTEGER,
    num_bundles INTEGER,
    control_system TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# 3. Создаём таблицу equipment (основная таблица оборудования)
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER NOT NULL,
    park_id INTEGER,
    model_id INTEGER,
    model TEXT,
    inv_number TEXT UNIQUE,
    serial_number TEXT,
    manufacturer TEXT,
    manufacture_date DATE,
    passport_file TEXT,
    manual_file TEXT,
    status TEXT DEFAULT 'in_rtu',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES equipment_types(id),
    FOREIGN KEY (park_id) REFERENCES parks(id)
)
""")

# 4. Создаём таблицу retarder_data (данные замедлителей)
cursor.execute("""
CREATE TABLE IF NOT EXISTS retarder_data (
    equipment_id INTEGER PRIMARY KEY,
    height_mm INTEGER,
    way TEXT,
    be TEXT DEFAULT '5067',
    network_number TEXT,
    os6_name TEXT,
    os6_install_year INTEGER,
    os6_last_repair INTEGER,
    os6_last_modernization INTEGER,
    tor_position TEXT,
    install_year INTEGER,
    last_repair_year INTEGER,
    total_operations INTEGER,
    avg_usage INTEGER,
    planned_repair_year INTEGER,
    residual_value REAL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
)
""")

# 5. Создаём таблицу equipment_location (местоположение)
cursor.execute("""
CREATE TABLE IF NOT EXISTS equipment_location (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL UNIQUE,
    track_section_id INTEGER,
    brake_position_id INTEGER,
    tor_position TEXT,
    mount_date DATE,
    mount_act_number TEXT,
    dismantle_date DATE,
    dismantle_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (track_section_id) REFERENCES track_sections(id),
    FOREIGN KEY (brake_position_id) REFERENCES brake_positions(id)
)
""")

# 6. Создаём таблицу movement_history (история перемещений)
cursor.execute("""
CREATE TABLE IF NOT EXISTS movement_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    from_status TEXT,
    to_status TEXT,
    from_location TEXT,
    to_location TEXT,
    movement_date DATE NOT NULL,
    act_number TEXT,
    responsible TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
)
""")

# 7. Добавляем начальные данные в equipment_types
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (1, 'Замедлитель', 'Торможение', '🛑')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (2, 'Стрелка', 'СЦБ', '🚉')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (3, 'Светофор', 'СЦБ', '🚦')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (4, 'Рельсовая цепь', 'Контроль', '🔌')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (5, 'ФЭУ-ИК', 'Диагностика', '📡')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (6, 'РТД-С', 'Диагностика', '📡')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (7, 'ИПД', 'Диагностика', '📊')")
cursor.execute("INSERT OR IGNORE INTO equipment_types (id, name, category, icon) VALUES (8, 'Управляющая аппаратура ВЗ', 'Управление', '🎛️')")

# 8. Добавляем парки
cursor.execute("INSERT OR IGNORE INTO parks (id, name, station, class) VALUES (1, 'СПСМ горка № 3', 'Санкт-Петербург - Сортировочный - Московский', 2)")
cursor.execute("INSERT OR IGNORE INTO parks (id, name, station, class) VALUES (2, 'СПСМ горка № 4', 'Санкт-Петербург - Сортировочный - Московский', 2)")
cursor.execute("INSERT OR IGNORE INTO parks (id, name, station, class) VALUES (3, 'Лужская', 'Лужская', 1)")
cursor.execute("INSERT OR IGNORE INTO parks (id, name, station, class) VALUES (4, 'Волховстрой', 'Волховстрой 1', 2)")
cursor.execute("INSERT OR IGNORE INTO parks (id, name, station, class) VALUES (5, 'Шушары', 'Шушары', 2)")

conn.commit()

# Проверяем созданные таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]
print("📋 Таблицы в БД:")
for t in tables:
    print(f"   - {t}")

conn.close()

print("\n✅ Недостающие таблицы созданы!")