# database.py
import sqlite3
from typing import List, Dict, Optional
from datetime import datetime

DB_PATH = "railway_equipment.db"


def get_db():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ============= ПАРКИ (ГОРКИ) =============
def get_parks() -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parks ORDER BY name")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_park_by_id(park_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parks WHERE id = ?", (park_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_park(name: str, station: str = None, park_class: int = None) -> int:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO parks (name, station, class) VALUES (?, ?, ?)
    """, (name, station, park_class))
    park_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return park_id


# ============= ТИПЫ ОБОРУДОВАНИЯ =============
def get_equipment_types() -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipment_types ORDER BY sort_order, name")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_equipment_type_id(name: str) -> Optional[int]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM equipment_types WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# ============= МОДЕЛИ ОБОРУДОВАНИЯ =============
def get_equipment_models(type_id: int = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    if type_id:
        cursor.execute("SELECT * FROM equipment_models WHERE type_id = ? ORDER BY name", (type_id,))
    else:
        cursor.execute("SELECT * FROM equipment_models ORDER BY name")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_model_by_name(type_id: int, name: str) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM equipment_models WHERE type_id = ? AND name = ?", (type_id, name))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_equipment_model(type_id: int, name: str, specs: dict = None) -> int:
    conn = get_db()
    cursor = conn.cursor()
    import json
    specs_json = json.dumps(specs, ensure_ascii=False) if specs else None
    cursor.execute("""
        INSERT INTO equipment_models (type_id, name, specs) VALUES (?, ?, ?)
    """, (type_id, name, specs_json))
    model_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return model_id


# ============= ОБОРУДОВАНИЕ =============
def get_all_equipment(equipment_type: str = None, park_id: int = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.*, et.name as type_name, et.icon, p.name as park_name,
               r.height_mm, r.way, r.total_operations, r.planned_repair_year
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        WHERE 1=1
    """
    params = []
    
    if equipment_type:
        query += " AND et.name = ?"
        params.append(equipment_type)
    if park_id:
        query += " AND e.park_id = ?"
        params.append(park_id)
    
    query += " ORDER BY e.id DESC"
    
    cursor.execute(query, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_equipment_by_id(equipment_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.*, et.name as type_name, et.icon, p.name as park_name,
               r.height_mm, r.way, r.be, r.network_number, r.os6_name,
               r.os6_install_year, r.os6_last_repair, r.os6_last_modernization,
               r.install_year, r.last_repair_year, r.total_operations, r.avg_usage,
               r.planned_repair_year, r.residual_value,
               loc.track_section_id, loc.brake_position_id, loc.tor_position, loc.mount_date
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        LEFT JOIN equipment_location loc ON e.id = loc.equipment_id
        WHERE e.id = ?
    """, (equipment_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def create_equipment(
    type_id: int,
    inv_number: str = None,
    serial_number: str = None,
    model: str = None,
    manufacturer: str = None,
    manufacture_date: str = None,
    park_id: int = None,
    status: str = 'in_rtu',
    notes: str = None
) -> int:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO equipment (type_id, park_id, inv_number, serial_number, 
                               manufacturer, manufacture_date, status, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (type_id, park_id, inv_number, serial_number, manufacturer, manufacture_date, status, notes))
    
    equipment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return equipment_id


def update_equipment(equipment_id: int, **kwargs):
    """Обновление полей оборудования"""
    conn = get_db()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(equipment_id)
        query = f"UPDATE equipment SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()


def update_equipment_status(equipment_id: int, status: str):
    """Обновить статус оборудования"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE equipment SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, equipment_id))
    conn.commit()
    conn.close()


# ============= ДАННЫЕ ЗАМЕДЛИТЕЛЕЙ =============
def create_retarder_data(
    equipment_id: int,
    height_mm: int = None,
    way: str = None,
    be: str = '5067',
    network_number: str = None,
    os6_name: str = None,
    os6_install_year: int = None,
    os6_last_repair: int = None,
    os6_last_modernization: int = None,
    install_year: int = None,
    last_repair_year: int = None,
    total_operations: int = None,
    avg_usage: int = None,
    planned_repair_year: int = None,
    residual_value: float = None
):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO retarder_data (
            equipment_id, height_mm, way, be, network_number,
            os6_name, os6_install_year, os6_last_repair, os6_last_modernization,
            install_year, last_repair_year, total_operations, avg_usage,
            planned_repair_year, residual_value
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (equipment_id, height_mm, way, be, network_number,
          os6_name, os6_install_year, os6_last_repair, os6_last_modernization,
          install_year, last_repair_year, total_operations, avg_usage,
          planned_repair_year, residual_value))
    conn.commit()
    conn.close()


def update_retarder_data(equipment_id: int, **kwargs):
    """Обновление данных замедлителя"""
    conn = get_db()
    cursor = conn.cursor()
    
    fields = []
    values = []
    for key, value in kwargs.items():
        if value is not None:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if fields:
        values.append(equipment_id)
        query = f"UPDATE retarder_data SET {', '.join(fields)} WHERE equipment_id = ?"
        cursor.execute(query, values)
        conn.commit()
    
    conn.close()


# ============= МЕСТОПОЛОЖЕНИЕ =============
def update_equipment_location(
    equipment_id: int,
    track_section_id: int = None,
    brake_position_id: int = None,
    tor_position: str = None,
    mount_date: str = None,
    mount_act_number: str = None
):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO equipment_location (
            equipment_id, track_section_id, brake_position_id, tor_position, mount_date, mount_act_number
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (equipment_id, track_section_id, brake_position_id, tor_position, mount_date, mount_act_number))
    
    conn.commit()
    conn.close()


# ============= СТАТИСТИКА =============
def get_statistics() -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM equipment")
    stats['total_equipment'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE type_id = 1")  # Замедлители
    stats['retarders'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status = 'active'")
    stats['active'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status = 'in_rtu'")
    stats['in_rtu'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE status = 'in_repair'")
    stats['in_repair'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM parks")
    stats['parks'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM track_sections")
    stats['sections'] = cursor.fetchone()[0]
    
    # По типам оборудования
    cursor.execute("""
        SELECT et.name, COUNT(*) 
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        GROUP BY et.name
        ORDER BY COUNT(*) DESC
    """)
    stats['by_type'] = cursor.fetchall()
    
    # По горкам
    cursor.execute("""
        SELECT p.name, COUNT(*) 
        FROM equipment e
        LEFT JOIN parks p ON e.park_id = p.id
        GROUP BY p.name
        ORDER BY COUNT(*) DESC
    """)
    stats['by_park'] = cursor.fetchall()
    
    # По статусам
    cursor.execute("SELECT status, COUNT(*) FROM equipment GROUP BY status")
    stats['by_status'] = dict(cursor.fetchall())
    
    # Требуют ремонта
    current_year = datetime.now().year
    cursor.execute("""
        SELECT COUNT(*) FROM retarder_data 
        WHERE planned_repair_year IS NOT NULL AND planned_repair_year <= ?
    """, (current_year,))
    stats['need_repair'] = cursor.fetchone()[0]
    
    conn.close()
    return stats


# ============= ВСПОМОГАТЕЛЬНЫЕ =============
def get_track_sections() -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM track_sections ORDER BY code")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_brake_positions() -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM brake_positions ORDER BY position_number")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


# database.py - добавить все недостающие функции в конец файла

# ============= ФУНКЦИИ ДЛЯ РОУТЕРОВ =============

def get_retarders(park_id: int = None, position: str = None) -> List[Dict]:
    """Получить список замедлителей"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.id, e.inv_number, e.serial_number, e.status, e.notes,
               e.model, e.manufacturer, e.manufacture_date,
               p.name as park_name, p.class as park_class,
               r.height_mm, r.way, r.install_year, r.last_repair_year,
               r.total_operations, r.planned_repair_year, r.residual_value,
               r.tor_position, r.be, r.network_number,
               loc.track_section_id, loc.brake_position_id, loc.mount_date
        FROM equipment e
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        LEFT JOIN equipment_location loc ON e.id = loc.equipment_id
        WHERE e.type_id = (SELECT id FROM equipment_types WHERE name = 'Замедлитель')
    """
    params = []
    
    if park_id:
        query += " AND e.park_id = ?"
        params.append(park_id)
    if position:
        query += " AND r.way = ?"
        params.append(position)
    
    query += " ORDER BY r.way, r.tor_position"
    
    cursor.execute(query, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_retarder_by_id(retarder_id: int) -> Optional[Dict]:
    """Получить замедлитель по ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.id, e.inv_number, e.serial_number, e.status, e.notes,
               e.model, e.manufacturer, e.manufacture_date,
               p.name as park_name, p.class as park_class,
               r.height_mm, r.way, r.install_year, r.last_repair_year,
               r.total_operations, r.planned_repair_year, r.residual_value,
               r.tor_position, r.be, r.network_number,
               loc.track_section_id, loc.brake_position_id, loc.mount_date,
               loc.tor_position as location_tor_position
        FROM equipment e
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        LEFT JOIN equipment_location loc ON e.id = loc.equipment_id
        WHERE e.id = ? AND e.type_id = (SELECT id FROM equipment_types WHERE name = 'Замедлитель')
    """, (retarder_id,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_retarder(retarder_id: int, data) -> bool:
    """Обновить замедлитель"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE equipment 
            SET model = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (getattr(data, 'model', None), getattr(data, 'notes', None), retarder_id))
        
        cursor.execute("""
            UPDATE retarder_data 
            SET height_mm = ?, install_year = ?, last_repair_year = ?,
                total_operations = ?, planned_repair_year = ?, residual_value = ?,
                tor_position = ?, way = ?
            WHERE equipment_id = ?
        """, (
            getattr(data, 'height_mm', None),
            getattr(data, 'install_year', None),
            getattr(data, 'last_repair_year', None),
            getattr(data, 'total_operations', None),
            getattr(data, 'planned_repair_year', None),
            getattr(data, 'residual_value', None),
            getattr(data, 'tor_position', None),
            getattr(data, 'way', None),
            retarder_id
        ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        conn.close()


def get_retarder_types() -> List[Dict]:
    """Получить типы замедлителей"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT model as name, model 
        FROM equipment 
        WHERE type_id = (SELECT id FROM equipment_types WHERE name = 'Замедлитель')
        AND model IS NOT NULL AND model != ''
        ORDER BY model
    """)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_switches(park_id: int = None) -> List[Dict]:
    """Получить список стрелок"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT c.id, c.serial_number, c.model, c.manufacturer, c.status,
               e.inv_number, e.notes,
               p.name as park_name,
               ts.name as section_name, ts.code as section_code
        FROM components c
        JOIN equipment e ON c.equipment_id = e.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN track_sections ts ON e.track_section_id = ts.id
        WHERE c.component_type_id IN (SELECT id FROM component_types WHERE name = 'Стрелка')
    """
    if park_id:
        query += " AND e.park_id = ?"
        cursor.execute(query, (park_id,))
    else:
        cursor.execute(query)
    
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_switch_by_id(switch_id: int) -> Optional[Dict]:
    """Получить стрелку по ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT c.id, c.serial_number, c.model, c.manufacturer, c.status,
               e.inv_number, e.notes, e.install_date,
               p.name as park_name,
               ts.name as section_name, ts.code as section_code
        FROM components c
        JOIN equipment e ON c.equipment_id = e.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN track_sections ts ON e.track_section_id = ts.id
        WHERE c.id = ?
    """, (switch_id,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_devices(device_type: str = None, park_id: int = None) -> List[Dict]:
    """Получить все устройства"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = """
        SELECT e.*, et.name as equipment_type_name, et.icon,
               p.name as park_name,
               r.height_mm, r.total_operations
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        WHERE 1=1
    """
    params = []
    
    if device_type:
        query += " AND et.name = ?"
        params.append(device_type)
    if park_id:
        query += " AND e.park_id = ?"
        params.append(park_id)
    
    query += " ORDER BY et.name, e.id"
    
    cursor.execute(query, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_device_by_id(device_id: int) -> Optional[Dict]:
    """Получить устройство по ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, et.name as equipment_type_name, et.icon,
               p.name as park_name,
               r.height_mm, r.total_operations, r.planned_repair_year
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data r ON e.id = r.equipment_id
        WHERE e.id = ?
    """, (device_id,))
    
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_components(device_id: int = None) -> List[Dict]:
    """Получить компоненты устройства"""
    conn = get_db()
    cursor = conn.cursor()
    
    if device_id:
        cursor.execute("""
            SELECT c.*, ct.name as component_type_name
            FROM components c
            JOIN component_types ct ON c.component_type_id = ct.id
            WHERE c.equipment_id = ?
            ORDER BY c.id
        """, (device_id,))
    else:
        cursor.execute("""
            SELECT c.*, ct.name as component_type_name
            FROM components c
            JOIN component_types ct ON c.component_type_id = ct.id
            ORDER BY c.component_type_id, c.id
        """)
    
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_parks() -> List[Dict]:
    """Получить список парков (горок)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parks ORDER BY name")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_park_by_id(park_id: int) -> Optional[Dict]:
    """Получить парк по ID"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM parks WHERE id = ?", (park_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_track_sections(park_id: int = None) -> List[Dict]:
    """Получить участки пути"""
    conn = get_db()
    cursor = conn.cursor()
    
    if park_id:
        cursor.execute("""
            SELECT ts.*, st.name as section_type_name, zt.name as zone_type_name
            FROM track_sections ts
            LEFT JOIN section_types st ON ts.section_type_id = st.id
            LEFT JOIN zone_types zt ON ts.zone_type_id = zt.id
            WHERE ts.park_id = ?
            ORDER BY ts.sort_order
        """, (park_id,))
    else:
        cursor.execute("""
            SELECT ts.*, st.name as section_type_name, zt.name as zone_type_name
            FROM track_sections ts
            LEFT JOIN section_types st ON ts.section_type_id = st.id
            LEFT JOIN zone_types zt ON ts.zone_type_id = zt.id
            ORDER BY ts.park_id, ts.sort_order
        """)
    
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_brake_positions(track_section_id: int = None) -> List[Dict]:
    """Получить тормозные позиции"""
    conn = get_db()
    cursor = conn.cursor()
    
    if track_section_id:
        cursor.execute("SELECT * FROM brake_positions WHERE track_section_id = ? ORDER BY position_number", (track_section_id,))
    else:
        cursor.execute("SELECT * FROM brake_positions ORDER BY position_number")
    
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result


def get_db():
    """Получить соединение с БД"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_statistics() -> Dict:
    """Получить статистику"""
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM equipment")
    stats['total_devices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment WHERE type_id = 1")
    stats['retarders'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM components WHERE component_type_id IN (SELECT id FROM component_types WHERE name = 'Стрелка')")
    stats['switches'] = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT et.name, COUNT(*) 
        FROM equipment e 
        JOIN equipment_types et ON e.type_id = et.id 
        GROUP BY et.name
    """)
    stats['by_type'] = cursor.fetchall()
    
    cursor.execute("""
        SELECT p.name, COUNT(*) 
        FROM equipment e 
        LEFT JOIN parks p ON e.park_id = p.id 
        GROUP BY p.name
    """)
    stats['by_park'] = cursor.fetchall()
    
    cursor.execute("SELECT status, COUNT(*) FROM equipment GROUP BY status")
    stats['by_status'] = dict(cursor.fetchall())
    
    cursor.execute("SELECT COUNT(*) FROM retarder_data WHERE planned_repair_year <= strftime('%Y', 'now')")
    stats['need_repair'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM track_sections")
    stats['track_sections'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM components")
    stats['components'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

def get_hierarchy_data() -> Dict:
    """Получить иерархические данные для визуализации"""
    conn = get_db()
    cursor = conn.cursor()
    
    parks = []
    cursor.execute("SELECT * FROM parks ORDER BY name")
    for park in cursor.fetchall():
        park_dict = dict(park)
        park_dict['track_sections'] = []
        
        # Получаем участки парка
        cursor.execute("""
            SELECT ts.*, st.name as section_type_name, zt.name as zone_type_name
            FROM track_sections ts
            LEFT JOIN section_types st ON ts.section_type_id = st.id
            LEFT JOIN zone_types zt ON ts.zone_type_id = zt.id
            WHERE ts.park_id = ? AND ts.is_active = 1
            ORDER BY ts.sort_order
        """, (park_dict['id'],))
        
        for section in cursor.fetchall():
            section_dict = dict(section)
            section_dict['devices'] = []
            
            # Получаем оборудование на участке
            cursor.execute("""
                SELECT e.*, et.name as type_name, et.icon,
                       r.height_mm, r.total_operations
                FROM equipment e
                JOIN equipment_types et ON e.type_id = et.id
                LEFT JOIN retarder_data r ON e.id = r.equipment_id
                WHERE e.track_section_id = ?
                ORDER BY e.id
            """, (section_dict['id'],))
            
            for device in cursor.fetchall():
                section_dict['devices'].append(dict(device))
            
            # Получаем тормозные позиции на участке
            cursor.execute("""
                SELECT * FROM brake_positions 
                WHERE track_section_id = ?
                ORDER BY position_number
            """, (section_dict['id'],))
            
            section_dict['brake_positions'] = [dict(bp) for bp in cursor.fetchall()]
            
            park_dict['track_sections'].append(section_dict)
        
        parks.append(park_dict)
    
    conn.close()
    return {"parks": parks}

# Добавьте в конец database.py

def get_equipment_models_by_type(type_id: int) -> List[Dict]:
    """Получить модели оборудования по типу"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, specs FROM equipment_models WHERE type_id = ? ORDER BY name", (type_id,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result