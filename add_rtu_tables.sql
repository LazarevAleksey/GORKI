-- add_rtu_tables.sql
-- Добавляем новые статусы для жизненного цикла
ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'in_rtu';
-- in_rtu, in_repair, active, reserve, written_off

-- Таблица партий поступления в РТУ
CREATE TABLE IF NOT EXISTS rtu_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_number TEXT NOT NULL UNIQUE,
    received_date DATE NOT NULL,
    supplier TEXT,
    invoice_number TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER
);

-- Таблица заказов на ремонт
CREATE TABLE IF NOT EXISTS repair_orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    repair_type TEXT NOT NULL,  -- 'planned', 'capital', 'current'
    reason TEXT,
    defects TEXT,
    received_date DATE NOT NULL,
    completed_date DATE,
    contractor TEXT,
    result TEXT,  -- 'repaired', 'scrapped', 'pending'
    act_number TEXT,
    cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Таблица заменённых компонентов при ремонте
CREATE TABLE IF NOT EXISTS replaced_parts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    repair_order_id INTEGER NOT NULL,
    part_type TEXT NOT NULL,  -- 'пневмокамера', 'тормозная шина', 'клапан', 'редуктор', 'БЭ', 'БУК'
    old_serial_number TEXT,
    new_serial_number TEXT,
    new_manufacturer TEXT,
    note TEXT,
    FOREIGN KEY (repair_order_id) REFERENCES repair_orders(id)
);

-- Таблица перемещений оборудования
CREATE TABLE IF NOT EXISTS device_movements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id INTEGER NOT NULL,
    from_location_type TEXT,  -- 'park', 'rtu', 'repair'
    from_location_id INTEGER,
    to_location_type TEXT,    -- 'park', 'rtu', 'repair'
    to_location_id INTEGER,
    movement_type TEXT NOT NULL,  -- 'receipt', 'installation', 'dismantling', 'transfer_to_repair', 'repair_complete'
    movement_date DATE NOT NULL,
    act_number TEXT,
    responsible TEXT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- Индексы
CREATE INDEX idx_repair_orders_device ON repair_orders(device_id);
CREATE INDEX idx_device_movements_device ON device_movements(device_id);
CREATE INDEX idx_devices_status ON devices(status);