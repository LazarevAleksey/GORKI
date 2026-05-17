# routers/rtu.py
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db
from utils.loaders import load_equipment_types, load_retarder_models, load_switch_models

router = APIRouter(prefix="/rtu", tags=["rtu"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def rtu_home(request: Request):
    """Главная страница РТУ"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Устройства в РТУ (не в ремонте)
    cursor.execute("""
        SELECT e.id, e.model, e.inv_number, e.serial_number, e.manufacturer,
               e.status, e.notes,
               et.name as type_name, et.icon,
               rd.height_mm
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN retarder_data rd ON e.id = rd.equipment_id
        WHERE e.status = 'in_rtu'
        AND NOT EXISTS (SELECT 1 FROM repair_history r WHERE r.equipment_id = e.id AND r.completed_date IS NULL)
        ORDER BY e.id DESC
    """)
    in_rtu = [dict(row) for row in cursor.fetchall()]
    
    # Устройства в ремонте
    cursor.execute("""
        SELECT e.id, e.model, e.inv_number, e.serial_number, e.status,
               et.name as type_name, et.icon, 
               r.id as repair_id, r.repair_type, r.defects, r.received_date as repair_date,
               rd.height_mm
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        JOIN repair_history r ON e.id = r.equipment_id
        LEFT JOIN retarder_data rd ON e.id = rd.equipment_id
        WHERE e.status = 'in_repair' AND r.completed_date IS NULL
        ORDER BY r.received_date DESC
    """)
    in_repair = [dict(row) for row in cursor.fetchall()]
    
    # Готовые к выдаче (отремонтированные)
    cursor.execute("""
        SELECT e.id, e.model, e.inv_number, e.serial_number, e.status,
               et.name as type_name, et.icon, r.completed_date,
               rd.height_mm
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        JOIN repair_history r ON e.id = r.equipment_id
        LEFT JOIN retarder_data rd ON e.id = rd.equipment_id
        WHERE e.status = 'in_rtu' AND r.completed_date IS NOT NULL
        ORDER BY r.completed_date DESC
    """)
    ready = [dict(row) for row in cursor.fetchall()]
    
    # Устройства на горках
    cursor.execute("""
        SELECT e.id, e.model, e.inv_number, e.serial_number, e.status,
               et.name as type_name, et.icon, p.name as park_name,
               rd.tor_position, rd.total_operations, rd.height_mm
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data rd ON e.id = rd.equipment_id
        WHERE e.status = 'active'
        ORDER BY e.id DESC
    """)
    active = [dict(row) for row in cursor.fetchall()]
    
    # Все устройства
    cursor.execute("""
        SELECT e.id, e.model, e.inv_number, e.serial_number, e.status,
               et.name as type_name, et.icon, p.name as park_name,
               rd.tor_position, rd.total_operations, rd.height_mm
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        LEFT JOIN retarder_data rd ON e.id = rd.equipment_id
        ORDER BY e.id DESC
    """)
    all_devices = [dict(row) for row in cursor.fetchall()]
    
    # Уникальные типы оборудования для фильтра
    cursor.execute("""
        SELECT DISTINCT et.id, et.name, et.icon 
        FROM equipment_types et
        JOIN equipment e ON e.type_id = et.id
        ORDER BY et.name
    """)
    equipment_types = [dict(row) for row in cursor.fetchall()]
    
    # Уникальные модели для фильтра
    cursor.execute("""
        SELECT DISTINCT model FROM equipment 
        WHERE model IS NOT NULL AND model != '' 
        ORDER BY model
    """)
    unique_models = [row[0] for row in cursor.fetchall()]
    
    # Уникальные горки для фильтра
    cursor.execute("""
        SELECT DISTINCT p.name FROM parks p
        JOIN equipment e ON e.park_id = p.id
        WHERE p.name IS NOT NULL
        ORDER BY p.name
    """)
    unique_parks = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    return templates.TemplateResponse("rtu.html", {
        "request": request,
        "in_rtu": in_rtu,
        "in_repair": in_repair,
        "ready": ready,
        "active": active,
        "all_devices": all_devices,
        "equipment_types": equipment_types,
        "unique_models": unique_models,
        "unique_parks": unique_parks
    })

# @router.get("/device/add", response_class=HTMLResponse)
# async def add_device_form(request: Request):
#     """Форма добавления оборудования в РТУ"""
#     conn = get_db()
#     cursor = conn.cursor()
#     # Загружаем данные из JSON файлов
#     # equipment_types = load_equipment_types()
#     cursor.execute("SELECT id, name, icon, specific_table FROM equipment_types ORDER BY name")
#     equipment_types = [{
#         "id": row[0], 
#         "name": row[1], 
#         "icon": row[2] or '',
#         "specific_table": row[3] or ''   # ← ДОБАВИТЬ
#         } for row in cursor.fetchall()]
#     retarder_models = load_retarder_models()
#     switch_models = load_switch_models()
    
#     return templates.TemplateResponse("rtu_device_add.html", {
#         "request": request,
#         "equipment_types": equipment_types,
#         "retarder_models": retarder_models,
#         "switch_models": switch_models
#     })


@router.get("/device/add", response_class=HTMLResponse)
async def add_device_form(request: Request):
    """Форма добавления оборудования в РТУ"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Типы оборудования из БД
    cursor.execute("SELECT id, name, icon, specific_table FROM equipment_types ORDER BY name")
    equipment_types = [{
        "id": row[0], 
        "name": row[1], 
        "icon": row[2] or '',
        "specific_table": row[3] or ''
    } for row in cursor.fetchall()]
    
    # 2. Модели замедлителей из БД (из таблицы equipment_models)
    cursor.execute("""
        SELECT id, name, manufacturer, emoji 
        FROM equipment_models 
        WHERE type_id = (SELECT id FROM equipment_types WHERE name = 'Замедлитель')
        ORDER BY name
    """)
    retarder_models = [{
        "id": row[0],
        "name": row[1],
        "manufacturer": row[2] or '',
        "emoji": row[3] or ''
    } for row in cursor.fetchall()]
    
    # 3. Модели стрелок (если есть таблица - берите из неё, пока статически)
    switch_models = [
        {"id": 1, "name": "Р65 1/9"},
        {"id": 2, "name": "Р65 1/11"},
        {"id": 3, "name": "Р50 1/9"}
    ]
    
    conn.close()
    
    return templates.TemplateResponse("rtu_device_add.html", {
        "request": request,
        "equipment_types": equipment_types,
        "retarder_models": retarder_models,
        "switch_models": switch_models
    })


@router.post("/device/add")
async def add_device(
    equipment_type_id: int = Form(...),
    model_id: int = Form(None),
    model_name: str = Form(None),
    serial_number: str = Form(...),
    inv_number: str = Form(None),
    height_mm: int = Form(None),
    manufacturer: str = Form(None),
    manufacture_date: str = Form(...),
    supplier: str = Form(None),
    notes: str = Form(""),
    network_number: str = Form(None),
    be: str = Form("5067"),
    os6_name: str = Form(None),
    os6_install_year: int = Form(None),
    os6_last_repair: int = Form(None),
    os6_last_modernization: int = Form(None),
    passport_number: str = Form(None),
    passport_date: str = Form(None),
    certificate_number: str = Form(None),
    certificate_expiry: str = Form(None),
    extra_params: str = Form(None)
):
    """Добавление оборудования в РТУ"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Если выбран замедлитель и есть model_id, получаем данные из JSON
    model_name_final = model_name
    height_mm_final = height_mm
    manufacturer_final = manufacturer or supplier
    
    if equipment_type_id == 1 and model_id:  # Замедлитель
        from utils.loaders import get_retarder_model_by_id
        model_data = get_retarder_model_by_id(model_id)
        if model_data:
            model_name_final = model_data.get('name')
            height_mm_final = model_data.get('height_mm')
            manufacturer_final = model_data.get('manufacturer')
    
    # Собираем паспортные данные в JSON
    passport_data = {}
    if passport_number:
        passport_data['passport_number'] = passport_number
    if passport_date:
        passport_data['passport_date'] = passport_date
    if certificate_number:
        passport_data['certificate_number'] = certificate_number
    if certificate_expiry:
        passport_data['certificate_expiry'] = certificate_expiry
    if extra_params:
        import json
        try:
            passport_data['extra_params'] = json.loads(extra_params)
        except:
            passport_data['extra_params'] = extra_params
    
    import json
    passport_json = json.dumps(passport_data, ensure_ascii=False) if passport_data else None
    
    try:
        cursor.execute("""
            INSERT INTO equipment (
                type_id, model, serial_number, inv_number, manufacturer,
                manufacture_date, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, 'in_rtu', ?)
        """, (equipment_type_id, model_name_final, serial_number, inv_number,
              manufacturer_final, manufacture_date, notes))
        
        equipment_id = cursor.lastrowid
        
        # Если это замедлитель, создаём запись в retarder_data
        if equipment_type_id == 1:  # Замедлитель
            cursor.execute("""
                INSERT INTO retarder_data (
                    equipment_id, height_mm, be, network_number,
                    os6_name, os6_install_year, os6_last_repair, os6_last_modernization
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (equipment_id, height_mm_final, be, network_number,
                  os6_name, os6_install_year, os6_last_repair, os6_last_modernization))
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{equipment_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()

@router.get("/device/{device_id}/repair", response_class=HTMLResponse)
async def repair_form(request: Request, device_id: int):
    """Форма отправки в ремонт"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, et.name as type_name
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        WHERE e.id = ?
    """, (device_id,))
    device = cursor.fetchone()
    
    conn.close()
    
    return templates.TemplateResponse("rtu_repair.html", {
        "request": request,
        "device": device
    })


@router.post("/device/{device_id}/repair")
async def start_repair(
    device_id: int,
    repair_type: str = Form(...),
    defects: str = Form(...),
    received_date: str = Form(...),
    reason: str = Form(None)
):
    """Начать ремонт устройства"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO repair_history (equipment_id, repair_type, reason, defects, received_date)
            VALUES (?, ?, ?, ?, ?)
        """, (device_id, repair_type, reason, defects, received_date))
        
        cursor.execute("UPDATE equipment SET status = 'in_repair' WHERE id = ?", (device_id,))
        
        conn.commit()
        return RedirectResponse(url=f"/rtu", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/device/{device_id}/install", response_class=HTMLResponse)
async def install_form(request: Request, device_id: int):
    """Форма установки на горку"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, et.name as type_name
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        WHERE e.id = ?
    """, (device_id,))
    device = cursor.fetchone()
    
    cursor.execute("SELECT id, name FROM parks ORDER BY name")
    parks = cursor.fetchall()
    
    cursor.execute("SELECT id, code, name FROM track_sections WHERE is_switch_section = 0 ORDER BY code")
    sections = cursor.fetchall()
    
    cursor.execute("SELECT id, position_number, position_type FROM brake_positions ORDER BY position_number")
    brake_positions = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("rtu_install.html", {
        "request": request,
        "device": device,
        "parks": parks,
        "sections": sections,
        "brake_positions": brake_positions
    })


@router.post("/device/{device_id}/install")
async def install_device(
    device_id: int,
    park_id: int = Form(...),
    track_section_id: int = Form(None),
    brake_position_id: int = Form(None),
    tor_position: str = Form(None),
    install_date: str = Form(...),
    act_number: str = Form(None)
):
    """Установка устройства на горку"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE equipment 
            SET park_id = ?, status = 'active'
            WHERE id = ?
        """, (park_id, device_id))
        
        # Обновляем местоположение
        cursor.execute("""
            INSERT OR REPLACE INTO equipment_location (
                equipment_id, track_section_id, brake_position_id, tor_position, mount_date, mount_act_number
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (device_id, track_section_id, brake_position_id, tor_position, install_date, act_number))
        
        # Если есть tor_position, обновляем в retarder_data
        if tor_position:
            cursor.execute("UPDATE retarder_data SET tor_position = ? WHERE equipment_id = ?", (tor_position, device_id))
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/device/{device_id}/dismantle", response_class=HTMLResponse)
async def dismantle_form(request: Request, device_id: int):
    """Форма демонтажа с горки"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT e.*, et.name as type_name, p.name as park_name
        FROM equipment e
        JOIN equipment_types et ON e.type_id = et.id
        LEFT JOIN parks p ON e.park_id = p.id
        WHERE e.id = ?
    """, (device_id,))
    device = cursor.fetchone()
    
    conn.close()
    
    return templates.TemplateResponse("rtu_dismantle.html", {
        "request": request,
        "device": device
    })


@router.post("/device/{device_id}/dismantle")
async def dismantle_device(
    device_id: int,
    dismantle_reason: str = Form(...),
    defects: str = Form(None),
    dismantle_date: str = Form(...),
    act_number: str = Form(None),
    destination: str = Form(...)
):
    """Демонтаж устройства с горки"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        if destination == 'rtu':
            cursor.execute("UPDATE equipment SET status = 'in_rtu', park_id = NULL WHERE id = ?", (device_id,))
        elif destination == 'scrap':
            cursor.execute("UPDATE equipment SET status = 'written_off', park_id = NULL WHERE id = ?", (device_id,))
        elif destination == 'reserve':
            cursor.execute("UPDATE equipment SET status = 'reserve', park_id = NULL WHERE id = ?", (device_id,))
        
        # Обновляем местоположение
        cursor.execute("""
            UPDATE equipment_location 
            SET dismantle_date = ?, dismantle_reason = ?
            WHERE equipment_id = ?
        """, (dismantle_date, dismantle_reason, device_id))
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()