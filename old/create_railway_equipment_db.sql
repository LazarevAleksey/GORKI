-- create_railway_equipment_db.sql
-- Чистый SQL скрипт без Python кода

-- 1. СПРАВОЧНИКИ
CREATE TABLE equipment_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    icon TEXT,
    has_passport BOOLEAN DEFAULT 1,
    has_serial_number BOOLEAN DEFAULT 1,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE component_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT,
    parent_type_id INTEGER,
    has_children BOOLEAN DEFAULT 1,
    icon TEXT,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (parent_type_id) REFERENCES component_types(id)
);

CREATE TABLE equipment_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    specs TEXT,
    manual_file TEXT,
    certificate_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (type_id) REFERENCES equipment_types(id),
    UNIQUE(type_id, name)
);

CREATE TABLE component_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_type_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    params TEXT,
    manual_file TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (component_type_id) REFERENCES component_types(id),
    UNIQUE(component_type_id, name)
);

-- 2. ТОПОЛОГИЯ ГОРКИ
CREATE TABLE parks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    station TEXT,
    class INTEGER,
    num_tracks INTEGER,
    num_bundles INTEGER,
    control_system TEXT,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE section_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE zone_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    sort_order INTEGER DEFAULT 0
);

CREATE TABLE track_sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    park_id INTEGER NOT NULL,
    section_type_id INTEGER NOT NULL,
    zone_type_id INTEGER,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    is_switch_section BOOLEAN DEFAULT 0,
    is_measuring_section BOOLEAN DEFAULT 0,
    is_brake_position BOOLEAN DEFAULT 0,
    brake_position_number INTEGER,
    brake_position_type TEXT,
    has_track_circuit BOOLEAN DEFAULT 0,
    has_axle_counter BOOLEAN DEFAULT 0,
    has_train_filling BOOLEAN DEFAULT 0,
    length_m REAL,
    sort_order INTEGER,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (park_id) REFERENCES parks(id),
    FOREIGN KEY (section_type_id) REFERENCES section_types(id),
    FOREIGN KEY (zone_type_id) REFERENCES zone_types(id)
);

CREATE TABLE brake_positions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    track_section_id INTEGER NOT NULL,
    position_number INTEGER NOT NULL,
    position_type TEXT,
    position_letter TEXT,
    max_speed_kmh REAL,
    num_retarders INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (track_section_id) REFERENCES track_sections(id)
);

-- 3. ОСНОВНАЯ ТАБЛИЦА ОБОРУДОВАНИЯ
CREATE TABLE equipment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type_id INTEGER NOT NULL,
    park_id INTEGER,
    model_id INTEGER,
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
    FOREIGN KEY (park_id) REFERENCES parks(id),
    FOREIGN KEY (model_id) REFERENCES equipment_models(id)
);

CREATE TABLE equipment_location (
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
);

-- 4. КОМПОНЕНТЫ
CREATE TABLE components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER,
    parent_component_id INTEGER,
    component_type_id INTEGER NOT NULL,
    model_id INTEGER,
    serial_number TEXT,
    manufacturer TEXT,
    manufacture_date DATE,
    params TEXT,
    passport_file TEXT,
    manual_file TEXT,
    status TEXT DEFAULT 'active',
    install_date DATE,
    replaced_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (parent_component_id) REFERENCES components(id),
    FOREIGN KEY (component_type_id) REFERENCES component_types(id),
    FOREIGN KEY (model_id) REFERENCES component_models(id)
);

-- 5. СПЕЦИФИЧНЫЕ ДАННЫЕ ДЛЯ ЗАМЕДЛИТЕЛЕЙ
CREATE TABLE retarder_data (
    equipment_id INTEGER PRIMARY KEY,
    height_mm INTEGER,
    way TEXT,
    be TEXT DEFAULT '5067',
    network_number TEXT,
    os6_name TEXT,
    os6_install_year INTEGER,
    os6_last_repair INTEGER,
    os6_last_modernization INTEGER,
    install_year INTEGER,
    last_repair_year INTEGER,
    total_operations INTEGER,
    avg_usage INTEGER,
    planned_repair_year INTEGER,
    residual_value REAL,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- 6. ФАЙЛЫ И ДОКУМЕНТЫ
CREATE TABLE equipment_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    file_name TEXT,
    file_path TEXT,
    file_size INTEGER,
    file_type TEXT,
    mime_type TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    uploaded_by INTEGER,
    description TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- 7. ЭКСПЛУАТАЦИОННЫЕ ДАННЫЕ
CREATE TABLE movement_history (
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
);

CREATE TABLE repair_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER NOT NULL,
    repair_type TEXT,
    defects TEXT,
    received_date DATE,
    completed_date DATE,
    contractor TEXT,
    cost REAL,
    act_number TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE TABLE replaced_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_id INTEGER NOT NULL,
    component_type TEXT,
    old_serial_number TEXT,
    new_serial_number TEXT,
    new_manufacturer TEXT,
    note TEXT,
    FOREIGN KEY (repair_id) REFERENCES repair_history(id)
);

-- 8. ПОЛЬЗОВАТЕЛЬСКИЕ ДАННЫЕ
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_favorites (
    user_id INTEGER,
    equipment_id INTEGER,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, equipment_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

CREATE TABLE user_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    equipment_id INTEGER,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (equipment_id) REFERENCES equipment(id)
);

-- 9. ИНДЕКСЫ
CREATE INDEX idx_equipment_type ON equipment(type_id);
CREATE INDEX idx_equipment_status ON equipment(status);
CREATE INDEX idx_equipment_inv ON equipment(inv_number);
CREATE INDEX idx_equipment_serial ON equipment(serial_number);
CREATE INDEX idx_equipment_park ON equipment(park_id);
CREATE INDEX idx_components_equipment ON components(equipment_id);
CREATE INDEX idx_components_parent ON components(parent_component_id);
CREATE INDEX idx_track_sections_park ON track_sections(park_id);
CREATE INDEX idx_equipment_location_equipment ON equipment_location(equipment_id);
CREATE INDEX idx_movement_history_equipment ON movement_history(equipment_id);
CREATE INDEX idx_repair_history_equipment ON repair_history(equipment_id);

-- 10. НАЧАЛЬНЫЕ ДАННЫЕ
INSERT OR IGNORE INTO equipment_types (name, category, icon, sort_order) VALUES
('Замедлитель', 'Торможение', '🛑', 1),
('Стрелка', 'СЦБ', '🚉', 2),
('Светофор', 'СЦБ', '🚦', 3),
('Рельсовая цепь', 'Контроль', '🔌', 4),
('ФЭУ-ИК', 'Диагностика', '📡', 5),
('РТД-С', 'Диагностика', '📡', 6),
('ИПД', 'Диагностика', '📊', 7),
('Управляющая аппаратура ВЗ', 'Управление', '🎛️', 8),
('Скоростемер', 'Измерение', '📈', 9),
('Индикатор веса', 'Измерение', '⚖️', 10),
('КЗП', 'СЦБ', '🔒', 11),
('УКВ', 'Связь', '📻', 12),
('Метеостанция', 'Диагностика', '🌤️', 13),
('Датчик счета осей', 'Контроль', '🔢', 14);

INSERT OR IGNORE INTO section_types (name, code, sort_order) VALUES
('надвижная часть', 'надвиг', 1),
('спускная часть', 'спуск', 2),
('парковая часть', 'парк', 3);

INSERT OR IGNORE INTO zone_types (name, code, sort_order) VALUES
('головная зона', 'голова', 1),
('пучковая зона', 'пучок', 2);