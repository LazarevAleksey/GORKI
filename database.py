import sqlite3
from typing import List, Dict, Optional

DB_PATH = "retarders_complete.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============= ПАРКИ =============
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

# ============= УЧАСТКИ =============
def get_track_sections(park_id: Optional[int] = None) -> List[Dict]:
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

def get_brake_positions(track_section_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    if track_section_id:
        cursor.execute("SELECT * FROM brake_positions WHERE track_section_id = ? ORDER BY position_number", (track_section_id,))
    else:
        cursor.execute("SELECT * FROM brake_positions ORDER BY position_number")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

# ============= ЗАМЕДЛИТЕЛИ =============
def get_retarders(park_id: Optional[int] = None, position: Optional[str] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT r.*, d.inv_number, d.serial_number, d.status, d.notes,
               p.name as park_name, p.class as park_class,
               ts.name as section_name, ts.code as section_code,
               bp.position_number, bp.position_type
        FROM retarders r
        JOIN devices d ON r.device_id = d.id
        LEFT JOIN parks p ON d.park_id = p.id
        LEFT JOIN track_sections ts ON d.track_section_id = ts.id
        LEFT JOIN brake_positions bp ON d.brake_position_id = bp.id
        WHERE 1=1
    """
    params = []
    if park_id:
        query += " AND d.park_id = ?"
        params.append(park_id)
    if position:
        query += " AND r.way = ?"
        params.append(position)
    query += " ORDER BY r.way, r.tor_position"
    cursor.execute(query, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

# def get_retarder_by_id(retarder_id: int) -> Optional[Dict]:
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute("""
#         SELECT r.*, d.inv_number, d.serial_number, d.status, d.notes, d.install_date,
#                p.name as park_name, p.class as park_class,
#                ts.name as section_name, ts.code as section_code,
#                bp.position_number, bp.position_type
#         FROM retarders r
#         JOIN devices d ON r.device_id = d.id
#         LEFT JOIN parks p ON d.park_id = p.id
#         LEFT JOIN track_sections ts ON d.track_section_id = ts.id
#         LEFT JOIN brake_positions bp ON d.brake_position_id = bp.id
#         WHERE r.id = ?
#     """, (retarder_id,))
#     row = cursor.fetchone()
#     conn.close()
#     return dict(row) if row else None

def get_retarder_by_id(retarder_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM retarders WHERE id = ?", (retarder_id,))
    retarder = cursor.fetchone()
    
    if not retarder:
        conn.close()
        return None
    
    retarder_dict = dict(retarder)
    
    # Получаем связанное устройство
    cursor.execute("SELECT * FROM devices WHERE id = ?", (retarder_dict['device_id'],))
    device = cursor.fetchone()
    if device:
        device_dict = dict(device)
        retarder_dict['inv_number'] = device_dict.get('inv_number', '')
        retarder_dict['serial_number'] = device_dict.get('serial_number', '')
        retarder_dict['status'] = device_dict.get('status', '')
        retarder_dict['install_date'] = device_dict.get('install_date', '')
        retarder_dict['notes'] = device_dict.get('notes', '')
        retarder_dict['park_id'] = device_dict.get('park_id', '')
        
        # Получаем парк
        if device_dict.get('park_id'):
            cursor.execute("SELECT name FROM parks WHERE id = ?", (device_dict['park_id'],))
            park = cursor.fetchone()
            retarder_dict['park_name'] = park['name'] if park else ''
    
    # Убеждаемся, что все поля есть
    for field in ['tor_position', 'way', 'notes', 'inv_number', 'serial_number', 'status', 'park_name']:
        if field not in retarder_dict:
            retarder_dict[field] = ''
    
    conn.close()
    return retarder_dict

def update_retarder(retarder_id: int, data) -> bool:
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE retarders 
            SET model = ?, height_mm = ?, install_year = ?, last_repair_year = ?,
                total_operations = ?, planned_repair_year = ?, residual_value = ?
            WHERE id = ?
        """, (data.model, data.height_mm, data.install_year, data.last_repair_year,
              data.total_operations, data.planned_repair_year, data.residual_value, retarder_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    finally:
        conn.close()

# ============= СТРЕЛКИ =============
def get_switches(park_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT s.*, d.inv_number, d.serial_number, d.status, d.model, d.location_detail,
               p.name as park_name,
               ts.name as section_name, ts.code as section_code
        FROM switches s
        JOIN devices d ON s.device_id = d.id
        LEFT JOIN parks p ON d.park_id = p.id
        LEFT JOIN track_sections ts ON d.track_section_id = ts.id
        WHERE 1=1
    """
    if park_id:
        query += " AND d.park_id = ?"
        cursor.execute(query, (park_id,))
    else:
        cursor.execute(query)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

def get_switch_by_id(switch_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.*, d.inv_number, d.serial_number, d.status, d.model, d.location_detail, d.install_date,
               p.name as park_name,
               ts.name as section_name, ts.code as section_code
        FROM switches s
        JOIN devices d ON s.device_id = d.id
        LEFT JOIN parks p ON d.park_id = p.id
        LEFT JOIN track_sections ts ON d.track_section_id = ts.id
        WHERE s.id = ?
    """, (switch_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# ============= ОБОРУДОВАНИЕ =============
def get_all_devices(device_type: Optional[str] = None, park_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    query = """
        SELECT d.*, et.name as equipment_type_name, et.icon,
               p.name as park_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        LEFT JOIN parks p ON d.park_id = p.id
        WHERE 1=1
    """
    params = []
    if device_type:
        query += " AND et.name = ?"
        params.append(device_type)
    if park_id:
        query += " AND d.park_id = ?"
        params.append(park_id)
    query += " ORDER BY et.name, d.id"
    cursor.execute(query, params)
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

def get_device_by_id(device_id: int) -> Optional[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.*, et.name as equipment_type_name, et.icon,
               p.name as park_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        LEFT JOIN parks p ON d.park_id = p.id
        WHERE d.id = ?
    """, (device_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_components(device_id: Optional[int] = None) -> List[Dict]:
    conn = get_db()
    cursor = conn.cursor()
    if device_id:
        cursor.execute("""
            SELECT * FROM components 
            WHERE parent_device_id = ? OR parent_component_id IN (SELECT id FROM components WHERE parent_device_id = ?)
            ORDER BY component_type
        """, (device_id, device_id))
    else:
        cursor.execute("SELECT * FROM components ORDER BY component_type")
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

# ============= СТАТИСТИКА =============
def get_statistics() -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    stats = {}
    
    cursor.execute("SELECT COUNT(*) FROM devices")
    stats['total_devices'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM retarders")
    stats['retarders'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM switches")
    stats['switches'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT et.name, COUNT(*) FROM devices d JOIN equipment_types et ON d.equipment_type_id = et.id GROUP BY et.name")
    stats['by_type'] = cursor.fetchall()
    
    cursor.execute("SELECT p.name, COUNT(*) FROM devices d LEFT JOIN parks p ON d.park_id = p.id GROUP BY p.name")
    stats['by_park'] = cursor.fetchall()
    
    cursor.execute("SELECT status, COUNT(*) FROM devices GROUP BY status")
    stats['by_status'] = dict(cursor.fetchall())
    
    cursor.execute("SELECT COUNT(*) FROM retarders WHERE planned_repair_year <= strftime('%Y', 'now')")
    stats['need_repair'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM track_sections")
    stats['track_sections'] = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM components")
    stats['components'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# ============= API ДЛЯ ВИЗУАЛИЗАЦИИ =============
def get_hierarchy_data() -> Dict:
    conn = get_db()
    cursor = conn.cursor()
    
    parks = []
    cursor.execute("SELECT * FROM parks")
    for park in cursor.fetchall():
        park_dict = dict(park)
        park_dict['track_sections'] = []
        
        cursor.execute("SELECT * FROM track_sections WHERE park_id = ? ORDER BY sort_order", (park_dict['id'],))
        for section in cursor.fetchall():
            section_dict = dict(section)
            section_dict['devices'] = []
            
            cursor.execute("""
                SELECT d.*, et.name as type_name 
                FROM devices d
                JOIN equipment_types et ON d.equipment_type_id = et.id
                WHERE d.track_section_id = ?
            """, (section_dict['id'],))
            for device in cursor.fetchall():
                section_dict['devices'].append(dict(device))
            
            park_dict['track_sections'].append(section_dict)
        
        parks.append(park_dict)
    
    conn.close()
    return {"parks": parks}