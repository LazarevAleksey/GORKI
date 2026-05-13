# routers/rtu.py
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from database import get_db
import json
from datetime import date
from utils.loaders import load_retarder_models, load_switch_models, load_equipment_types, get_retarder_model_by_id

router = APIRouter(prefix="/rtu", tags=["rtu"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def rtu_home(request: Request):
    """Главная страница РТУ"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Устройства в РТУ
    cursor.execute("""
        SELECT d.*, et.name as type_name, et.icon
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        WHERE d.status = 'in_rtu'
        AND NOT EXISTS (SELECT 1 FROM repair_orders r WHERE r.device_id = d.id AND r.completed_date IS NULL)
        ORDER BY d.id DESC
    """)
    in_rtu = cursor.fetchall()
    
    # Устройства в ремонте
    cursor.execute("""
        SELECT d.*, et.name as type_name, et.icon, r.id as repair_id, r.repair_type, r.defects, r.received_date as repair_date
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        JOIN repair_orders r ON d.id = r.device_id
        WHERE d.status = 'in_repair' AND r.completed_date IS NULL
        ORDER BY r.received_date DESC
    """)
    in_repair = cursor.fetchall()
    
    # Готовые к выдаче
    cursor.execute("""
        SELECT d.*, et.name as type_name, et.icon, r.completed_date
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        JOIN repair_orders r ON d.id = r.device_id
        WHERE d.status = 'in_rtu' AND r.completed_date IS NOT NULL
        ORDER BY r.completed_date DESC
    """)
    ready = cursor.fetchall()
    
    # Устройства на горках
    cursor.execute("""
        SELECT d.*, et.name as type_name, et.icon, p.name as park_name,
               rd.tor_position, rd.total_operations
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        LEFT JOIN parks p ON d.park_id = p.id
        LEFT JOIN retarders rd ON d.id = rd.device_id
        WHERE d.status = 'active'
        ORDER BY d.id DESC
    """)
    active = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("rtu.html", {
        "request": request,
        "in_rtu": in_rtu,
        "in_repair": in_repair,
        "ready": ready,
        "active": active
    })


@router.get("/batch/add", response_class=HTMLResponse)
async def add_batch_form(request: Request):
    """Форма добавления новой партии"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM equipment_types WHERE name IN ('Замедлитель', 'Стрелка', 'ИПД')")
    equipment_types = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("rtu_batch_add.html", {
        "request": request,
        "equipment_types": equipment_types
    })


@router.post("/batch/add")
async def add_batch(
    batch_number: str = Form(...),
    received_date: str = Form(...),
    supplier: str = Form(None),
    invoice_number: str = Form(None),
    notes: str = Form("")
):
    """Сохранение новой партии"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO rtu_batches (batch_number, received_date, supplier, invoice_number, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (batch_number, received_date, supplier, invoice_number, notes))
        batch_id = cursor.lastrowid
        conn.commit()
        
        return RedirectResponse(url=f"/rtu/batch/{batch_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/batch/{batch_id}", response_class=HTMLResponse)
async def batch_detail(request: Request, batch_id: int):
    """Детали партии"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rtu_batches WHERE id = ?", (batch_id,))
    batch = cursor.fetchone()
    
    cursor.execute("""
        SELECT d.*, et.name as type_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        WHERE d.rtu_batch_id = ?
    """, (batch_id,))
    devices = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("rtu_batch_detail.html", {
        "request": request,
        "batch": batch,
        "devices": devices
    })


@router.post("/batch/{batch_id}/add_device")
async def add_device_to_batch(
    batch_id: int,
    equipment_type_id: int = Form(...),
    model: str = Form(...),
    serial_number: str = Form(None),
    inv_number: str = Form(None),
    height_mm: int = Form(None)
):
    """Добавление устройства в партию"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO devices (equipment_type_id, model, serial_number, inv_number, height_mm, status, rtu_batch_id)
            VALUES (?, ?, ?, ?, ?, 'in_rtu', ?)
        """, (equipment_type_id, model, serial_number, inv_number, height_mm, batch_id))
        
        device_id = cursor.lastrowid
        
        # Записываем перемещение
        cursor.execute("""
            INSERT INTO device_movements (device_id, to_location_type, to_location_id, movement_type, movement_date)
            VALUES (?, 'rtu', ?, 'receipt', date('now'))
        """, (device_id, batch_id))
        
        # Если это замедлитель, создаём запись в retarders
        cursor.execute("SELECT name FROM equipment_types WHERE id = ?", (equipment_type_id,))
        eq_type = cursor.fetchone()
        if eq_type and eq_type[0] == 'Замедлитель':
            cursor.execute("""
                INSERT INTO retarders (device_id, model, height_mm)
                VALUES (?, ?, ?)
            """, (device_id, model, height_mm))
        
        conn.commit()
        return RedirectResponse(url=f"/rtu/batch/{batch_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/device/{device_id}/repair", response_class=HTMLResponse)
async def repair_form(request: Request, device_id: int):
    """Форма отправки в ремонт"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT d.*, et.name as type_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        WHERE d.id = ?
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
        # Создаём заказ на ремонт
        cursor.execute("""
            INSERT INTO repair_orders (device_id, repair_type, reason, defects, received_date, result)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (device_id, repair_type, reason, defects, received_date))
        repair_id = cursor.lastrowid
        
        # Обновляем статус устройства
        cursor.execute("UPDATE devices SET status = 'in_repair' WHERE id = ?", (device_id,))
        
        # Записываем перемещение
        cursor.execute("""
            INSERT INTO device_movements (device_id, from_location_type, to_location_type, movement_type, movement_date)
            VALUES (?, 'rtu', 'repair', 'transfer_to_repair', ?)
        """, (device_id, received_date))
        
        conn.commit()
        return RedirectResponse(url=f"/rtu/repair/{repair_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/repair/{repair_id}", response_class=HTMLResponse)
async def repair_detail(request: Request, repair_id: int):
    """Детали ремонта"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, d.model, d.inv_number, d.serial_number, et.name as type_name
        FROM repair_orders r
        JOIN devices d ON r.device_id = d.id
        JOIN equipment_types et ON d.equipment_type_id = et.id
        WHERE r.id = ?
    """, (repair_id,))
    repair = cursor.fetchone()
    
    cursor.execute("SELECT * FROM replaced_parts WHERE repair_order_id = ?", (repair_id,))
    replaced_parts = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("rtu_repair_detail.html", {
        "request": request,
        "repair": repair,
        "replaced_parts": replaced_parts
    })


@router.post("/repair/{repair_id}/complete")
async def complete_repair(
    repair_id: int,
    completed_date: str = Form(...),
    result: str = Form(...),
    contractor: str = Form(None),
    act_number: str = Form(None),
    cost: float = Form(None)
):
    """Завершение ремонта"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE repair_orders 
            SET completed_date = ?, result = ?, contractor = ?, act_number = ?, cost = ?
            WHERE id = ?
        """, (completed_date, result, contractor, act_number, cost, repair_id))
        
        cursor.execute("SELECT device_id FROM repair_orders WHERE id = ?", (repair_id,))
        device_id = cursor.fetchone()[0]
        
        if result == 'repaired':
            cursor.execute("UPDATE devices SET status = 'in_rtu' WHERE id = ?", (device_id,))
        elif result == 'scrapped':
            cursor.execute("UPDATE devices SET status = 'written_off' WHERE id = ?", (device_id,))
        
        cursor.execute("""
            INSERT INTO device_movements (device_id, from_location_type, to_location_type, movement_type, movement_date)
            VALUES (?, 'repair', 'rtu', 'repair_complete', ?)
        """, (device_id, completed_date))
        
        conn.commit()
        return RedirectResponse(url=f"/rtu/repair/{repair_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.post("/repair/{repair_id}/add_part")
async def add_replaced_part(
    repair_id: int,
    part_type: str = Form(...),
    old_serial_number: str = Form(None),
    new_serial_number: str = Form(None),
    new_manufacturer: str = Form(None),
    note: str = Form("")
):
    """Добавить заменённый компонент"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO replaced_parts (repair_order_id, part_type, old_serial_number, new_serial_number, new_manufacturer, note)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (repair_id, part_type, old_serial_number, new_serial_number, new_manufacturer, note))
        conn.commit()
        return RedirectResponse(url=f"/rtu/repair/{repair_id}", status_code=303)
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
        SELECT d.*, et.name as type_name, p.name as park_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        LEFT JOIN parks p ON d.park_id = p.id
        WHERE d.id = ?
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
    destination: str = Form(...)  # 'rtu', 'scrap', 'reserve'
):
    """Демонтаж устройства с горки"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Записываем перемещение
        cursor.execute("""
            INSERT INTO device_movements (device_id, from_location_type, movement_type, movement_date, act_number, notes)
            VALUES (?, 'park', 'dismantling', ?, ?, ?)
        """, (device_id, dismantle_date, act_number, defects))
        
        if destination == 'rtu':
            cursor.execute("UPDATE devices SET status = 'in_rtu', park_id = NULL, track_section_id = NULL WHERE id = ?", (device_id,))
        elif destination == 'scrap':
            cursor.execute("UPDATE devices SET status = 'written_off', park_id = NULL WHERE id = ?", (device_id,))
        elif destination == 'reserve':
            cursor.execute("UPDATE devices SET status = 'reserve', park_id = NULL WHERE id = ?", (device_id,))
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
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
        SELECT d.*, et.name as type_name
        FROM devices d
        JOIN equipment_types et ON d.equipment_type_id = et.id
        WHERE d.id = ?
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
            UPDATE devices 
            SET park_id = ?, track_section_id = ?, brake_position_id = ?, status = 'active', install_date = ?
            WHERE id = ?
        """, (park_id, track_section_id, brake_position_id, install_date, device_id))
        
        # Если есть tor_position, обновляем в retarders
        if tor_position:
            cursor.execute("UPDATE retarders SET tor_position = ? WHERE device_id = ?", (tor_position, device_id))
        
        # Записываем перемещение
        cursor.execute("""
            INSERT INTO device_movements (device_id, to_location_type, to_location_id, movement_type, movement_date, act_number)
            VALUES (?, 'park', ?, 'installation', ?, ?)
        """, (device_id, park_id, install_date, act_number))
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()


@router.get("/device/add", response_class=HTMLResponse)
async def add_device_form(request: Request):
    equipment_types = load_equipment_types()
    retarder_models = load_retarder_models()
    switch_models = load_switch_models()
    
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
    serial_number: str = Form(None),
    inv_number: str = Form(None),
    height_mm: int = Form(None),
    manufacturer: str = Form(None),
    manufacture_date: str = Form(None),
    supplier: str = Form(None),
    passport_number: str = Form(None),
    passport_date: str = Form(None),
    certificate_number: str = Form(None),
    certificate_expiry: str = Form(None),
    extra_params: str = Form(None),
    notes: str = Form(""),
    # НОВЫЕ ПОЛЯ:
    network_number: str = Form(None),
    be: str = Form("5067"),
    os6_name: str = Form(None),
    os6_install_year: int = Form(None),
    os6_last_repair: int = Form(None),
    os6_last_modernization: int = Form(None)
):
    """Добавление оборудования в РТУ"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Логируем полученные данные для отладки
    print(f"equipment_type_id: {equipment_type_id}")
    print(f"model_id: {model_id}")
    print(f"model_name: {model_name}")
    
    # Если выбран замедлитель и есть model_id, получаем данные из справочника
    if equipment_type_id == 1 and model_id:  # 1 - Замедлитель
        from utils.loaders import get_retarder_model_by_id
        model_data = get_retarder_model_by_id(model_id)
        if model_data:
            model_name = model_data["name"]
            height_mm = model_data["height_mm"]
            if not manufacturer:
                manufacturer = model_data["manufacturer"]
            print(f"Загружена модель: {model_name}, высота: {height_mm}")
    
    # Собираем паспортные данные
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
        # Вставляем в devices
        cursor.execute("""
            INSERT INTO devices (
                equipment_type_id, model, serial_number, inv_number, height_mm,
                manufacturer, manufacture_date, passport_data, notes, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_rtu')
        """, (equipment_type_id, model_name, serial_number, inv_number, height_mm,
              manufacturer or supplier, manufacture_date, passport_json, notes))
        
        device_id = cursor.lastrowid
        print(f"Создано устройство с ID: {device_id}")
        
        # Записываем перемещение
        cursor.execute("""
            INSERT INTO device_movements (device_id, to_location_type, movement_type, movement_date)
            VALUES (?, 'rtu', 'receipt', date('now'))
        """, (device_id,))
        
        # Если это замедлитель, создаём запись в retarders
        if equipment_type_id == 1:  # Замедлитель
            cursor.execute("""
                INSERT INTO retarders (device_id, model, height_mm)
                VALUES (?, ?, ?)
            """, (device_id, model_name, height_mm))
            print(f"Создана запись в retarders для device_id: {device_id}")
        
        conn.commit()
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        print(f"Ошибка: {e}")
        raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
    finally:
        conn.close()

# @router.post("/device/add")
# async def add_device(
#     equipment_type_id: int = Form(...),
#     model_id: int = Form(None),
#     model_name: str = Form(None),
#     serial_number: str = Form(None),
#     inv_number: str = Form(None),
#     height_mm: int = Form(None),
#     manufacturer: str = Form(None),
#     manufacture_date: str = Form(None),
#     supplier: str = Form(None),
#     passport_number: str = Form(None),
#     passport_date: str = Form(None),
#     certificate_number: str = Form(None),
#     certificate_expiry: str = Form(None),
#     extra_params: str = Form(None),
#     notes: str = Form("")
# ):
#     """Добавление оборудования в РТУ"""
#     conn = get_db()
#     cursor = conn.cursor()
    
#     # Если выбрана модель из справочника, подставляем её параметры
#     if model_id and equipment_type_id == 1:  # Замедлитель
#         model_data = get_retarder_model_by_id(model_id)
#         if model_data:
#             model_name = model_data["name"]
#             height_mm = model_data["height_mm"]
#             if not manufacturer:
#                 manufacturer = model_data["manufacturer"]
    
#     # Собираем паспортные данные
#     passport_data = {}
#     if passport_number:
#         passport_data['passport_number'] = passport_number
#     if passport_date:
#         passport_data['passport_date'] = passport_date
#     if certificate_number:
#         passport_data['certificate_number'] = certificate_number
#     if certificate_expiry:
#         passport_data['certificate_expiry'] = certificate_expiry
#     if extra_params:
#         import json
#         try:
#             passport_data['extra_params'] = json.loads(extra_params)
#         except:
#             passport_data['extra_params'] = extra_params
    
#     import json
#     passport_json = json.dumps(passport_data, ensure_ascii=False) if passport_data else None
    
#     try:
#         cursor.execute("""
#             INSERT INTO devices (
#                 equipment_type_id, model, serial_number, inv_number, height_mm,
#                 manufacturer, manufacture_date, passport_data, notes, status
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'in_rtu')
#         """, (equipment_type_id, model_name, serial_number, inv_number, height_mm,
#               manufacturer or supplier, manufacture_date, passport_json, notes))
        
#         device_id = cursor.lastrowid
        
#         # Записываем перемещение
#         cursor.execute("""
#             INSERT INTO device_movements (device_id, to_location_type, movement_type, movement_date)
#             VALUES (?, 'rtu', 'receipt', date('now'))
#         """, (device_id,))
        
#         # Если это замедлитель, создаём запись в retarders
#         if equipment_type_id == 1:  # Замедлитель
#             cursor.execute("""
#                 INSERT INTO retarders (device_id, model, height_mm)
#                 VALUES (?, ?, ?)
#             """, (device_id, model_name, height_mm))
        
#         conn.commit()
#         return RedirectResponse(url=f"/rtu", status_code=303)
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=f"Ошибка: {e}")
#     finally:
#         conn.close()


