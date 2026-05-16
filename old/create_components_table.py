# create_components_table.py
import sqlite3

DB_PATH = "railway_equipment.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS components (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    equipment_id INTEGER,
    parent_component_id INTEGER,
    component_type_id INTEGER,
    model_id INTEGER,
    serial_number TEXT,
    manufacturer TEXT,
    manufacture_date DATE,
    params TEXT,
    status TEXT DEFAULT 'active',
    install_date DATE,
    notes TEXT,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (parent_component_id) REFERENCES components(id)
)
""")

conn.commit()
conn.close()
print("✅ Таблица components создана")