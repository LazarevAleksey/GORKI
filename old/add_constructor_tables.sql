-- add_constructor_tables.sql
-- Скрипт для добавления таблиц конструктора горок

-- Таблица для шаблонов горок
CREATE TABLE IF NOT EXISTS park_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    is_default BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для элементов шаблона
CREATE TABLE IF NOT EXISTS template_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id INTEGER NOT NULL,
    element_type TEXT NOT NULL,  -- 'section', 'brake_position', 'switch_section'
    parent_id INTEGER,          -- для вложенности (например, участок внутри зоны)
    section_type_id INTEGER,    -- ссылка на section_types
    zone_type_id INTEGER,       -- ссылка на zone_types
    name TEXT,
    code TEXT,
    sort_order INTEGER,
    params TEXT,                -- JSON с параметрами (длина, ширина и т.д.)
    FOREIGN KEY (template_id) REFERENCES park_templates(id),
    FOREIGN KEY (section_type_id) REFERENCES section_types(id),
    FOREIGN KEY (zone_type_id) REFERENCES zone_types(id)
);

-- Таблица для сохранённых схем горок (на основе шаблонов)
CREATE TABLE IF NOT EXISTS park_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    park_id INTEGER NOT NULL,
    template_id INTEGER,
    data TEXT NOT NULL,         -- полный JSON схемы
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT 1,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    saved_by INTEGER,
    FOREIGN KEY (park_id) REFERENCES parks(id),
    FOREIGN KEY (template_id) REFERENCES park_templates(id)
);

-- Индексы
CREATE INDEX IF NOT EXISTS idx_template_elements_template ON template_elements(template_id);
CREATE INDEX IF NOT EXISTS idx_park_schemes_park ON park_schemes(park_id);

-- Проверка создания таблиц
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('park_templates', 'template_elements', 'park_schemes');