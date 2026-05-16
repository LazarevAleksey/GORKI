# fix_db.py
import sqlite3

DB_PATH = "retarders.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Проверяем существующие таблицы
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Существующие таблицы:", tables)

# Удаляем старые таблицы, если нужно пересоздать
cursor.execute("DROP TABLE IF EXISTS retarders")
cursor.execute("DROP TABLE IF EXISTS parks")
cursor.execute("DROP TABLE IF EXISTS devices")
cursor.execute("DROP TABLE IF EXISTS brake_positions")
cursor.execute("DROP TABLE IF EXISTS retarder_types")

# Создаём таблицу parks
cursor.execute("""
    CREATE TABLE IF NOT EXISTS parks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        class INTEGER,
        station TEXT
    )
""")

# Создаём таблицу retarder_types
cursor.execute("""
    CREATE TABLE IF NOT EXISTS retarder_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        height_mm INTEGER,
        max_speed_kmh REAL,
        manufacturer TEXT
    )
""")

# Создаём основную таблицу retarders с правильными колонками
cursor.execute("""
    CREATE TABLE IF NOT EXISTS retarders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        height_mm INTEGER,
        inv_number TEXT UNIQUE,
        serial_number TEXT,
        tor_position TEXT,
        way TEXT,
        install_year INTEGER,
        last_repair_year INTEGER,
        last_modernization_year INTEGER,
        total_operations INTEGER,
        avg_usage INTEGER,
        planned_repair_year INTEGER,
        residual_value REAL,
        status TEXT DEFAULT 'active',
        notes TEXT,
        park_id INTEGER,
        retarder_type_id INTEGER,
        FOREIGN KEY (park_id) REFERENCES parks(id),
        FOREIGN KEY (retarder_type_id) REFERENCES retarder_types(id)
    )
""")

# Добавляем парки (горки)
parks_data = [
    ('СПСМ горка № 3', 2, 'Санкт-Петербург - Сортировочный - Московский'),
    ('СПСМ горка № 4', 2, 'Санкт-Петербург - Сортировочный - Московский'),
    ('Лужская', 1, 'Лужская'),
    ('Волховстрой', 2, 'Волховстрой 1'),
    ('Шушары', 2, 'Шушары')
]

for park in parks_data:
    cursor.execute("INSERT OR IGNORE INTO parks (name, class, station) VALUES (?, ?, ?)", park)

# Добавляем типы замедлителей
types_data = [
    ('КЗ-3ПК', 600, 30.6, 'АО "АМЗ"'),
    ('КЗ-5ПК', 600, 32.4, 'АО "АМЗ"'),
    ('КНЗ-3ПК', 900, 30.6, 'АО "АМЗ"'),
    ('КНЗ-5ПК', 900, 32.4, 'АО "АМЗ"'),
    ('КНП-5', 1130, 18.0, 'АО "АМЗ"'),
    ('TW-4F', 600, 32.4, 'ThyssenKrupp'),
    ('TW-5EF', 600, 36.0, 'ThyssenKrupp'),
    ('TKG16', 600, 14.4, 'ThyssenKrupp'),
    ('ВЗКН-5', 900, 27.0, 'АО "АМЗ"'),
    ('КВ-3', 600, 25.2, 'АО "АМЗ"')
]

for r_type in types_data:
    cursor.execute("INSERT OR IGNORE INTO retarder_types (name, height_mm, max_speed_kmh, manufacturer) VALUES (?, ?, ?, ?)", r_type)

# Добавляем тестовые замедлители
test_retarders = [
    ('КЗ-3ПК', 600, '044414/3А06', None, '1 ВТП', '1', 2010, 2020, None, 911284, 1711440, 2020, 4406664.62, 'active', None, 1, 1),
    ('КЗ-3ПК', 600, '044415/3А06', None, '2 ВТП', '1', 2010, 2020, None, 1400290, 1711440, 2020, 4016867.3, 'active', None, 1, 1),
    ('КНЗ-5ПК', 900, '044375/3А06', None, '1 НТП', '3', 2010, None, None, 300516, 30051.6, None, 4265003.68, 'active', None, 1, 4),
]

for r in test_retarders:
    try:
        cursor.execute("""
            INSERT INTO retarders (
                model, height_mm, inv_number, serial_number, tor_position, way,
                install_year, last_repair_year, last_modernization_year,
                total_operations, avg_usage, planned_repair_year, residual_value,
                status, notes, park_id, retarder_type_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, r)
    except sqlite3.IntegrityError:
        print(f"Замедлитель {r[2]} уже существует")

conn.commit()

# Проверяем результат
cursor.execute("SELECT COUNT(*) FROM retarders")
count = cursor.fetchone()[0]
print(f"\n✅ База данных готова! В таблице retarders: {count} записей")

cursor.execute("SELECT id, name FROM parks")
for row in cursor.fetchall():
    print(f"   Парк: {row[1]} (id={row[0]})")

conn.close()
print("\n✅ Готово!")