-- Создание таблицы моделей замедлителей
CREATE TABLE IF NOT EXISTS retarder_models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    height_mm INTEGER,
    manufacturer TEXT,
    max_speed_kmh REAL,
    capacity_thousand_operations INTEGER
);

-- Добавление стандартных моделей
INSERT OR IGNORE INTO retarder_models (name, height_mm, manufacturer) VALUES
('КЗ-3ПК', 600, 'АО "АМЗ"'),
('КЗ-5ПК', 600, 'АО "АМЗ"'),
('КНЗ-3ПК', 900, 'АО "АМЗ"'),
('КНЗ-5ПК', 900, 'АО "АМЗ"'),
('КНП-5', 1130, 'АО "АМЗ"'),
('ВЗКН-5', 900, 'АО "АМЗ"'),
('TW-4F', 600, 'ThyssenKrupp'),
('TW-5EF', 600, 'ThyssenKrupp'),
('TKG16', 600, 'ThyssenKrupp');