# create_complete_db.py
import sqlite3
import os

DB_PATH = "retarders_complete.db"

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print("🗑️ Старая БД удалена")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# =====================================================
# 1. ПАРКИ (ГОРКИ)
# =====================================================
cursor.execute("""
    CREATE TABLE parks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        station TEXT,
        class INTEGER,
        num_tracks INTEGER,
        num_bundles INTEGER,
        control_system TEXT,
        description TEXT
    )
""")

# =====================================================
# 2. ТИПЫ УЧАСТКОВ
# =====================================================
cursor.execute("""
    CREATE TABLE section_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE
    )
""")

cursor.execute("""
    CREATE TABLE zone_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        code TEXT UNIQUE
    )
""")

# =====================================================
# 3. УЧАСТКИ ПУТИ (топология горки)
# =====================================================
cursor.execute("""
    CREATE TABLE track_sections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        park_id INTEGER NOT NULL,
        section_type_id INTEGER NOT NULL,
        zone_type_id INTEGER,
        
        name TEXT NOT NULL,
        code TEXT UNIQUE,
        description TEXT,
        
        kilometer REAL,
        start_pk REAL,
        end_pk REAL,
        length_m REAL,
        
        is_switch_section BOOLEAN DEFAULT 0,
        is_measuring_section BOOLEAN DEFAULT 0,
        has_track_circuit BOOLEAN DEFAULT 0,
        has_axle_counter BOOLEAN DEFAULT 0,
        has_train_filling BOOLEAN DEFAULT 0,
        
        sort_order INTEGER,
        is_active BOOLEAN DEFAULT 1,
        
        FOREIGN KEY (park_id) REFERENCES parks(id),
        FOREIGN KEY (section_type_id) REFERENCES section_types(id),
        FOREIGN KEY (zone_type_id) REFERENCES zone_types(id)
    )
""")

# =====================================================
# 4. ТОРМОЗНЫЕ ПОЗИЦИИ
# =====================================================
cursor.execute("""
    CREATE TABLE brake_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        track_section_id INTEGER NOT NULL,
        position_number INTEGER NOT NULL,
        position_type TEXT,
        position_letter TEXT,
        max_speed_kmh REAL,
        num_retarders INTEGER DEFAULT 1,
        
        FOREIGN KEY (track_section_id) REFERENCES track_sections(id)
    )
""")

# =====================================================
# 5. ТИПЫ ОБОРУДОВАНИЯ
# =====================================================
cursor.execute("""
    CREATE TABLE equipment_types (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        category TEXT,
        icon TEXT,
        has_passport BOOLEAN DEFAULT 1,
        has_serial_number BOOLEAN DEFAULT 1
    )
""")

# =====================================================
# 6. ОСНОВНАЯ ТАБЛИЦА УСТРОЙСТВ
# =====================================================
cursor.execute("""
    CREATE TABLE devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        equipment_type_id INTEGER NOT NULL,
        park_id INTEGER,
        track_section_id INTEGER,
        brake_position_id INTEGER,
        
        model TEXT,
        inv_number TEXT UNIQUE,
        serial_number TEXT,
        
        location_detail TEXT,
        mount_date DATE,
        
        params TEXT,
        
        manufacture_date DATE,
        install_date DATE,
        last_check_date DATE,
        
        status TEXT DEFAULT 'active',
        notes TEXT,
        
        FOREIGN KEY (equipment_type_id) REFERENCES equipment_types(id),
        FOREIGN KEY (park_id) REFERENCES parks(id),
        FOREIGN KEY (track_section_id) REFERENCES track_sections(id),
        FOREIGN KEY (brake_position_id) REFERENCES brake_positions(id)
    )
""")

# =====================================================
# 7. ЗАМЕДЛИТЕЛИ (специфичные поля)
# =====================================================
cursor.execute("""
    CREATE TABLE retarders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        model TEXT,
        height_mm INTEGER,
        tor_position TEXT,
        way TEXT,
        install_year INTEGER,
        last_repair_year INTEGER,
        last_modernization_year INTEGER,
        total_operations INTEGER,
        avg_usage INTEGER,
        planned_repair_year INTEGER,
        residual_value REAL,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 8. СТРЕЛКИ (специфичные поля)
# =====================================================
cursor.execute("""
    CREATE TABLE switches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        switch_number TEXT,
        switch_type TEXT,
        rail_type TEXT,
        has_electric_drive BOOLEAN DEFAULT 1,
        has_switch_heating BOOLEAN DEFAULT 0,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 9. СВЕТОФОРЫ (специфичные поля)
# =====================================================
cursor.execute("""
    CREATE TABLE traffic_lights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        light_number TEXT,
        light_type TEXT,
        lamp_type TEXT,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 10. РЕЛЬСОВЫЕ ЦЕПИ
# =====================================================
cursor.execute("""
    CREATE TABLE track_circuits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        circuit_type TEXT,
        frequency REAL,
        voltage REAL,
        length_m REAL,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 11. ДАТЧИКИ (ФЭУ-ИК, РТД-С, скоростемеры, весы, счет осей)
# =====================================================
cursor.execute("""
    CREATE TABLE sensors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        sensor_type TEXT,
        model TEXT,
        accuracy REAL,
        last_calibration_date DATE,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 12. ИПД (измерительный преобразователь)
# =====================================================
cursor.execute("""
    CREATE TABLE ipd (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        has_be BOOLEAN DEFAULT 0,
        has_surge_protection BOOLEAN DEFAULT 0,
        has_loop BOOLEAN DEFAULT 0,
        has_commutation BOOLEAN DEFAULT 0,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 13. УПРАВЛЯЮЩАЯ АППАРАТУРА ВЗ
# =====================================================
cursor.execute("""
    CREATE TABLE control_gear (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL UNIQUE,
        
        has_buk BOOLEAN DEFAULT 0,
        has_valves BOOLEAN DEFAULT 0,
        has_rdk BOOLEAN DEFAULT 0,
        has_temp_regulator BOOLEAN DEFAULT 0,
        has_surge_protection BOOLEAN DEFAULT 0,
        
        controlled_retarders TEXT,
        
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# 14. КОМПОНЕНТЫ (СЭП, редуктор, двигатель, БЭ, БУК и т.д.)
# =====================================================
cursor.execute("""
    CREATE TABLE components (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        parent_device_id INTEGER,
        parent_component_id INTEGER,
        
        component_type TEXT NOT NULL,
        model TEXT,
        serial_number TEXT,
        manufacturer TEXT,
        batch_number TEXT,
        
        manufacture_date DATE,
        install_date DATE,
        params TEXT,
        
        status TEXT DEFAULT 'active',
        notes TEXT,
        
        FOREIGN KEY (parent_device_id) REFERENCES devices(id),
        FOREIGN KEY (parent_component_id) REFERENCES components(id)
    )
""")

# =====================================================
# 15. ЖУРНАЛ ПРОВЕРОК
# =====================================================
cursor.execute("""
    CREATE TABLE inspections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        component_id INTEGER,
        
        inspection_date DATE NOT NULL,
        inspection_type TEXT,
        result TEXT,
        defects TEXT,
        measurements TEXT,
        inspector TEXT,
        act_number TEXT,
        
        was_replaced BOOLEAN DEFAULT 0,
        new_component_id INTEGER,
        
        FOREIGN KEY (device_id) REFERENCES devices(id),
        FOREIGN KEY (component_id) REFERENCES components(id),
        FOREIGN KEY (new_component_id) REFERENCES components(id)
    )
""")

# =====================================================
# 16. ИСТОРИЯ ИЗМЕНЕНИЙ
# =====================================================
cursor.execute("""
    CREATE TABLE change_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER,
        component_id INTEGER,
        user_id INTEGER,
        field_name TEXT,
        old_value TEXT,
        new_value TEXT,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# =====================================================
# 17. ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ
# =====================================================
cursor.execute("""
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        full_name TEXT,
        role TEXT DEFAULT 'user'
    )
""")

cursor.execute("""
    CREATE TABLE user_favorites (
        user_id INTEGER,
        device_id INTEGER,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, device_id),
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (device_id) REFERENCES devices(id)
    )
""")

# =====================================================
# ЗАПОЛНЯЕМ СПРАВОЧНИКИ
# =====================================================

# Типы участков
cursor.execute("INSERT INTO section_types (name, code) VALUES (?, ?)", ('надвижная часть', 'надвиг'))
cursor.execute("INSERT INTO section_types (name, code) VALUES (?, ?)", ('спускная часть', 'спуск'))
cursor.execute("INSERT INTO section_types (name, code) VALUES (?, ?)", ('парковая часть', 'парк'))

# Типы зон
cursor.execute("INSERT INTO zone_types (name, code) VALUES (?, ?)", ('головная зона', 'голова'))
cursor.execute("INSERT INTO zone_types (name, code) VALUES (?, ?)", ('пучковая зона', 'пучок'))

# Типы оборудования
equipment_types = [
    ('Замедлитель', 'Торможение', '🛑', 1, 1),
    ('Стрелка', 'СЦБ', '🚉', 1, 1),
    ('Светофор', 'СЦБ', '🚦', 1, 1),
    ('Рельсовая цепь', 'Контроль', '🔌', 1, 1),
    ('ФЭУ-ИК', 'Диагностика', '📡', 1, 1),
    ('РТД-С', 'Диагностика', '📡', 1, 1),
    ('ИПД', 'Диагностика', '📊', 1, 1),
    ('Управляющая аппаратура ВЗ', 'Управление', '🎛️', 1, 1),
    ('Скоростемер', 'Измерение', '📈', 1, 1),
    ('Индикатор веса', 'Измерение', '⚖️', 1, 1),
    ('КЗП', 'СЦБ', '🔒', 1, 1),
    ('УКВ', 'Связь', '📻', 1, 1),
    ('Метеостанция', 'Диагностика', '🌤️', 1, 1),
    ('Датчик счета осей', 'Контроль', '🔢', 1, 1),
]

for et in equipment_types:
    cursor.execute("INSERT INTO equipment_types (name, category, icon, has_passport, has_serial_number) VALUES (?, ?, ?, ?, ?)", et)

# Парки (горки)
parks = [
    ('СПСМ горка № 3', 'Санкт-Петербург - Сортировочный - Московский', 2, 32, 2, 'КСАУ СП', 'Основная горка'),
    ('СПСМ горка № 4', 'Санкт-Петербург - Сортировочный - Московский', 2, 35, 3, 'БГАЦ', 'Резервная горка'),
    ('Лужская', 'Лужская', 1, 44, 3, 'MSR32', 'Импортное оборудование'),
    ('Волховстрой', 'Волховстрой 1', 2, 8, 1, 'БГАЦ', 'Малая горка'),
    ('Шушары', 'Шушары', 2, 15, 2, None, 'Старого типа'),
]

for p in parks:
    cursor.execute("INSERT INTO parks (name, station, class, num_tracks, num_bundles, control_system, description) VALUES (?, ?, ?, ?, ?, ?, ?)", p)

# =====================================================
# ДОБАВЛЯЕМ ТОПОЛОГИЮ ДЛЯ СПСМ горка № 3
# =====================================================

park_id = 1
section_type_nadvig = 1
section_type_spusk = 2
section_type_park = 3
zone_golova = 1
zone_puchok = 2

# Надвижная часть
cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_nadvig, 'Путь надвига 1', 'НП-1', 0, 1, 1))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_nadvig, 'Путь надвига 2', 'НП-2', 0, 1, 2))

# Стрелочные участки надвижной части
cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_nadvig, 'Стрелочный участок 1', 'НП-С1', 1, 1, 10))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_nadvig, 'Стрелочный участок 2', 'НП-С2', 1, 1, 11))

# Головная зона спускной части
cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, has_track_circuit, has_axle_counter, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_golova, 'Скоростной участок', 'ГЗ-СУ', 1, 0, 1))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, is_measuring_section, has_track_circuit, has_axle_counter, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_golova, 'Измерительный участок', 'ГЗ-ИУ', 1, 1, 1, 2))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_golova, 'Стрелочная зона', 'ГЗ-СЗ', 1, 1, 3))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_golova, '1 тормозная позиция', 'ГЗ-1ТП', 1, 4))

# Пучковая зона спускной части
cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, has_track_circuit, has_axle_counter, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_puchok, 'Бесстрелочный участок', 'ПЗ-БУ', 1, 1, 1))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, is_switch_section, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_puchok, 'Стрелочная зона', 'ПЗ-СЗ', 1, 1, 2))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, zone_type_id, name, code, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_spusk, zone_puchok, '2 тормозная позиция', 'ПЗ-2ТП', 1, 3))

# Парковая часть
cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, has_track_circuit, has_axle_counter, has_train_filling, sort_order)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""", (park_id, section_type_park, 'Бесстрелочный участок', 'ПП-БУ', 1, 1, 1, 1))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?)
""", (park_id, section_type_park, '3 тормозная позиция', 'ПП-3ТП', 1, 2))

cursor.execute("""
    INSERT INTO track_sections (park_id, section_type_id, name, code, has_track_circuit, sort_order)
    VALUES (?, ?, ?, ?, ?, ?)
""", (park_id, section_type_park, '4 тормозная позиция', 'ПП-4ТП', 1, 3))

# Сортировочные пути парковой части (201-232)
for i in range(201, 233):
    cursor.execute("""
        INSERT INTO track_sections (park_id, section_type_id, name, code, has_track_circuit, has_axle_counter, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (park_id, section_type_park, f'Путь {i}', f'П-{i}', 1, 1, i))

# =====================================================
# ДОБАВЛЯЕМ ТОРМОЗНЫЕ ПОЗИЦИИ
# =====================================================

# 1 тормозная позиция (ВТП)
cursor.execute("SELECT id FROM track_sections WHERE code = 'ГЗ-1ТП'")
tp1_id = cursor.fetchone()[0]
cursor.execute("""
    INSERT INTO brake_positions (track_section_id, position_number, position_type, max_speed_kmh, num_retarders)
    VALUES (?, 1, 'ВТП', 25, 2)
""", (tp1_id,))

# 2 тормозная позиция (СТП)
cursor.execute("SELECT id FROM track_sections WHERE code = 'ПЗ-2ТП'")
tp2_id = cursor.fetchone()[0]
cursor.execute("""
    INSERT INTO brake_positions (track_section_id, position_number, position_type, max_speed_kmh, num_retarders)
    VALUES (?, 2, 'СТП', 20, 12)
""", (tp2_id,))

# 3 тормозная позиция (НТП)
cursor.execute("SELECT id FROM track_sections WHERE code = 'ПП-3ТП'")
tp3_id = cursor.fetchone()[0]
cursor.execute("""
    INSERT INTO brake_positions (track_section_id, position_number, position_type, max_speed_kmh, num_retarders)
    VALUES (?, 3, 'НТП', 15, 15)
""", (tp3_id,))

# 4 тормозная позиция (НТП)
cursor.execute("SELECT id FROM track_sections WHERE code = 'ПП-4ТП'")
tp4_id = cursor.fetchone()[0]
cursor.execute("""
    INSERT INTO brake_positions (track_section_id, position_number, position_type, max_speed_kmh, num_retarders)
    VALUES (?, 4, 'НТП', 15, 15)
""", (tp4_id,))

# =====================================================
# ДОБАВЛЯЕМ ТЕСТОВЫЕ УСТРОЙСТВА
# =====================================================

def get_equipment_type_id(name):
    cursor.execute("SELECT id FROM equipment_types WHERE name = ?", (name,))
    return cursor.fetchone()[0]

def get_section_id(code):
    cursor.execute("SELECT id FROM track_sections WHERE code = ?", (code,))
    return cursor.fetchone()[0]

# Замедлители
retarder_data = [
    ('КЗ-3ПК', '044414/3А06', '1 ВТП', '1', 600, 2010, 2020, 911284, 2020, 4406664.62, 'ГЗ-1ТП'),
    ('КЗ-3ПК', '044415/3А06', '2 ВТП', '1', 600, 2010, 2020, 1400290, 2020, 4016867.3, 'ГЗ-1ТП'),
    ('КНЗ-5ПК', '044375/3А06', '1 НТП', '3', 900, 2010, 0, 300516, 0, 4265003.68, 'ПП-3ТП'),
]

for rd in retarder_data:
    section_id = get_section_id(rd[10])
    cursor.execute("SELECT id FROM brake_positions WHERE track_section_id = ? AND position_type = ?", (section_id, rd[10].split('-')[1]))
    bp_row = cursor.fetchone()
    brake_pos_id = bp_row[0] if bp_row else None
    
    cursor.execute("""
        INSERT INTO devices (equipment_type_id, park_id, track_section_id, brake_position_id, model, inv_number, status)
        VALUES (?, ?, ?, ?, ?, ?, 'active')
    """, (get_equipment_type_id('Замедлитель'), park_id, section_id, brake_pos_id, rd[0], rd[1]))
    device_id = cursor.lastrowid
    
    cursor.execute("""
        INSERT INTO retarders (device_id, model, height_mm, tor_position, way, install_year, last_repair_year, total_operations, planned_repair_year, residual_value)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (device_id, rd[0], rd[4], rd[2], rd[3], rd[5], rd[6], rd[7], rd[8], rd[9]))

# Светофор
cursor.execute("""
    INSERT INTO devices (equipment_type_id, park_id, track_section_id, model, inv_number, location_detail, status)
    VALUES (?, ?, ?, ?, ?, ?, 'active')
""", (get_equipment_type_id('Светофор'), park_id, get_section_id('НП-1'), 'Светофор Н1', 'СВ-001', 'вход'))
light_id = cursor.lastrowid
cursor.execute("INSERT INTO traffic_lights (device_id, light_number, light_type) VALUES (?, ?, ?)", (light_id, 'Н1', 'входной'))

# Рельсовая цепь
cursor.execute("""
    INSERT INTO devices (equipment_type_id, park_id, track_section_id, model, inv_number, status)
    VALUES (?, ?, ?, ?, ?, 'active')
""", (get_equipment_type_id('Рельсовая цепь'), park_id, get_section_id('НП-1'), 'РЦ-50Гц', 'РЦ-001'))
rc_id = cursor.lastrowid
cursor.execute("INSERT INTO track_circuits (device_id, circuit_type, frequency) VALUES (?, ?, ?)", (rc_id, '50Гц', 50))

# ФЭУ-ИК
cursor.execute("""
    INSERT INTO devices (equipment_type_id, park_id, track_section_id, model, inv_number, status)
    VALUES (?, ?, ?, ?, ?, 'active')
""", (get_equipment_type_id('ФЭУ-ИК'), park_id, get_section_id('ГЗ-ИУ'), 'ФЭУ-ИК', 'ФЭУ-001'))
feu_id = cursor.lastrowid
cursor.execute("INSERT INTO sensors (device_id, sensor_type, model) VALUES (?, ?, ?)", (feu_id, 'feu', 'ФЭУ-ИК'))

# Скоростемер
cursor.execute("""
    INSERT INTO devices (equipment_type_id, park_id, track_section_id, model, inv_number, status)
    VALUES (?, ?, ?, ?, ?, 'active')
""", (get_equipment_type_id('Скоростемер'), park_id, get_section_id('ГЗ-ИУ'), 'Скоростемер', 'СП-001'))
spd_id = cursor.lastrowid
cursor.execute("INSERT INTO sensors (device_id, sensor_type, model) VALUES (?, ?, ?)", (spd_id, 'speedometer', 'Скоростемер-М'))

# Управляющая аппаратура ВЗ
cursor.execute("""
    INSERT INTO devices (equipment_type_id, park_id, model, inv_number, status)
    VALUES (?, ?, ?, ?, 'active')
""", (get_equipment_type_id('Управляющая аппаратура ВЗ'), park_id, 'БУК-01', 'БУК-001'))
cg_id = cursor.lastrowid
cursor.execute("""
    INSERT INTO control_gear (device_id, has_buk, has_valves, has_rdk, has_temp_regulator, has_surge_protection)
    VALUES (?, ?, ?, ?, ?, ?)
""", (cg_id, 1, 1, 1, 1, 1))

# Компоненты (СЭП, редуктор, двигатель)
cursor.execute("""
    INSERT INTO components (parent_device_id, component_type, model, serial_number, manufacturer, install_date)
    VALUES ((SELECT id FROM devices WHERE equipment_type_id = ? LIMIT 1), 'СЭП', 'СЭП-4М', 'СЭП-2024-001', 'АО "АМЗ"', '2024-01-15')
""", (get_equipment_type_id('Стрелка'),))
sep_id = cursor.lastrowid

cursor.execute("""
    INSERT INTO components (parent_component_id, component_type, model, serial_number, manufacturer, install_date)
    VALUES (?, 'Редуктор', 'Р-2024', 'Р-2024-001', 'АО "АМЗ"', '2024-01-15')
""", (sep_id,))

cursor.execute("""
    INSERT INTO components (parent_component_id, component_type, model, serial_number, manufacturer, install_date)
    VALUES (?, 'Двигатель', 'Д-2024', 'Д-2024-001', 'ООО "Электромаш"', '2024-01-15')
""", (sep_id,))

# =====================================================
# ФИНАЛЬНЫЕ ДАННЫЕ
# =====================================================
conn.commit()

print("\n" + "="*50)
print("📊 СТАТИСТИКА БАЗЫ ДАННЫХ")
print("="*50)

cursor.execute("SELECT COUNT(*) FROM parks")
print(f"   🏭 Парки (горки): {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM track_sections")
print(f"   🛤️ Участки пути: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM brake_positions")
print(f"   🛑 Тормозные позиции: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM equipment_types")
print(f"   📦 Типы оборудования: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM devices")
print(f"   📟 Устройства: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM retarders")
print(f"   🚂 Замедлители: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM switches")
print(f"   🚉 Стрелки: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM traffic_lights")
print(f"   🚦 Светофоры: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM track_circuits")
print(f"   🔌 Рельсовые цепи: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM sensors")
print(f"   📡 Датчики: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM components")
print(f"   🔧 Компоненты: {cursor.fetchone()[0]}")

cursor.execute("SELECT COUNT(*) FROM control_gear")
print(f"   🎛️ Управляющая аппаратура: {cursor.fetchone()[0]}")

conn.close()

print("\n✅ База данных создана: retarders_complete.db")