# from fastapi import APIRouter, Request, HTTPException, Form
# from fastapi.responses import HTMLResponse, RedirectResponse
# from fastapi.templating import Jinja2Templates
# from database import get_all_devices, get_device_by_id, get_components, get_parks, get_db

# router = APIRouter(prefix="/devices", tags=["devices"])
# templates = Jinja2Templates(directory="templates")

# # @router.get("/", response_class=HTMLResponse)
# # async def devices_list(request: Request, device_type: str = None, park_id: int = None):
# #     devices = get_all_devices(device_type, park_id)
# #     parks = get_parks()
# #     return templates.TemplateResponse("devices.html", {
# #         "request": request, "devices": devices, "parks": parks,
# #         "selected_type": device_type, "selected_park": park_id
# #     })

# @router.get("/", response_class=HTMLResponse)
# async def devices_list(request: Request, device_type: str = None, park_id: int = None):
#     devices = get_all_devices(device_type, park_id)
#     parks = get_parks()
    
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute("SELECT DISTINCT name FROM equipment_types ORDER BY name")
#     types = [row[0] for row in cursor.fetchall()]
#     conn.close()
    
#     return templates.TemplateResponse("devices.html", {
#         "request": request, "devices": devices, "parks": parks, "types": types,
#         "selected_type": device_type, "selected_park": park_id
#     })

# @router.get("/{device_id}", response_class=HTMLResponse)
# async def device_detail(request: Request, device_id: int):
#     device = get_device_by_id(device_id)
#     if not device:
#         raise HTTPException(status_code=404, detail="Устройство не найдено")
#     components = get_components(device_id)
#     return templates.TemplateResponse("device_detail.html", {
#         "request": request, "device": device, "components": components
#     })

# # routers/devices.py - добавить в конец файла

# @router.get("/add", response_class=HTMLResponse)
# async def device_add_form(request: Request):
#     """Форма добавления нового устройства"""
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name, icon FROM equipment_types ORDER BY name")
#     equipment_types = cursor.fetchall()
#     cursor.execute("SELECT id, name FROM parks ORDER BY name")
#     parks = cursor.fetchall()
#     cursor.execute("SELECT id, name, code FROM track_sections ORDER BY name")
#     sections = cursor.fetchall()
#     cursor.execute("SELECT id, position_number, position_type FROM brake_positions")
#     brake_positions = cursor.fetchall()
#     conn.close()

#     return templates.TemplateResponse("device_add.html", {
#         "request": request,
#         "equipment_types": equipment_types,
#         "parks": parks,
#         "sections": sections,
#         "brake_positions": brake_positions
#     })

# @router.post("/add")
# async def device_add(
#     request: Request,
#     equipment_type_id: int = Form(...),
#     park_id: int = Form(None),
#     track_section_id: int = Form(None),
#     brake_position_id: int = Form(None),
#     model: str = Form(...),
#     inv_number: str = Form(None),
#     serial_number: str = Form(None),
#     location_detail: str = Form(None),
#     install_date: str = Form(None),
#     manufacture_date: str = Form(None),
#     status: str = Form("active"),
#     notes: str = Form("")
# ):
#     """Сохранение нового устройства"""
#     conn = get_db()
#     cursor = conn.cursor()
    
#     try:
#         cursor.execute("""
#             INSERT INTO devices (
#                 equipment_type_id, park_id, track_section_id, brake_position_id,
#                 model, inv_number, serial_number, location_detail,
#                 install_date, manufacture_date, status, notes
#             ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         """, (equipment_type_id, park_id, track_section_id, brake_position_id,
#               model, inv_number, serial_number, location_detail,
#               install_date, manufacture_date, status, notes))
#         conn.commit()
#         device_id = cursor.lastrowid
        
#         # Если это замедлитель, создаём запись в таблице retarders
#         cursor.execute("SELECT name FROM equipment_types WHERE id = ?", (equipment_type_id,))
#         eq_type = cursor.fetchone()
#         if eq_type and eq_type[0] == 'Замедлитель':
#             cursor.execute("""
#                 INSERT INTO retarders (device_id, model) VALUES (?, ?)
#             """, (device_id, model))
#             conn.commit()
        
#         # Если это стрелка, создаём запись в таблице switches
#         if eq_type and eq_type[0] == 'Стрелка':
#             cursor.execute("""
#                 INSERT INTO switches (device_id, switch_number, switch_type) VALUES (?, ?, ?)
#             """, (device_id, model, model))
#             conn.commit()
        
#         return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=f"Ошибка при добавлении: {e}")
#     finally:
#         conn.close()

# @router.get("/{device_id}/edit", response_class=HTMLResponse)
# async def device_edit_form(request: Request, device_id: int):
#     """Форма редактирования устройства"""
#     device = get_device_by_id(device_id)
#     if not device:
#         raise HTTPException(status_code=404, detail="Устройство не найдено")
    
#     conn = get_db()
#     cursor = conn.cursor()
#     cursor.execute("SELECT id, name, icon FROM equipment_types ORDER BY name")
#     equipment_types = cursor.fetchall()
#     cursor.execute("SELECT id, name FROM parks ORDER BY name")
#     parks = cursor.fetchall()
#     cursor.execute("SELECT id, name, code FROM track_sections ORDER BY name")
#     sections = cursor.fetchall()
#     cursor.execute("SELECT id, position_number, position_type FROM brake_positions")
#     brake_positions = cursor.fetchall()
#     conn.close()
    
#     return templates.TemplateResponse("device_edit.html", {
#         "request": request,
#         "device": device,
#         "equipment_types": equipment_types,
#         "parks": parks,
#         "sections": sections,
#         "brake_positions": brake_positions
#     })

# @router.post("/{device_id}/edit")
# async def device_edit(
#     request: Request,
#     device_id: int,
#     equipment_type_id: int = Form(...),
#     park_id: int = Form(None),
#     track_section_id: int = Form(None),
#     brake_position_id: int = Form(None),
#     model: str = Form(...),
#     inv_number: str = Form(None),
#     serial_number: str = Form(None),
#     location_detail: str = Form(None),
#     install_date: str = Form(None),
#     manufacture_date: str = Form(None),
#     status: str = Form(...),
#     notes: str = Form("")
# ):
#     """Сохранение изменений устройства"""
#     conn = get_db()
#     cursor = conn.cursor()
    
#     try:
#         cursor.execute("""
#             UPDATE devices SET
#                 equipment_type_id = ?, park_id = ?, track_section_id = ?, brake_position_id = ?,
#                 model = ?, inv_number = ?, serial_number = ?, location_detail = ?,
#                 install_date = ?, manufacture_date = ?, status = ?, notes = ?
#             WHERE id = ?
#         """, (equipment_type_id, park_id, track_section_id, brake_position_id,
#               model, inv_number, serial_number, location_detail,
#               install_date, manufacture_date, status, notes, device_id))
#         conn.commit()
        
#         return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=f"Ошибка при обновлении: {e}")
#     finally:
#         conn.close()

# @router.post("/{device_id}/delete")
# async def device_delete(device_id: int):
#     """Удаление устройства (мягкое)"""
#     conn = get_db()
#     cursor = conn.cursor()
    
#     try:
#         cursor.execute("UPDATE devices SET status = 'written_off' WHERE id = ?", (device_id,))
#         conn.commit()
#         return RedirectResponse(url="/devices", status_code=303)
#     except Exception as e:
#         conn.rollback()
#         raise HTTPException(status_code=400, detail=f"Ошибка при удалении: {e}")
#     finally:
#         conn.close()
# routers/devices.py - полностью исправленный файл

from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_all_devices, get_device_by_id, get_components, get_parks, get_db

router = APIRouter(prefix="/devices", tags=["devices"])
templates = Jinja2Templates(directory="templates")


# ============= СТАТИЧЕСКИЕ МАРШРУТЫ (без параметров) =============

@router.get("/", response_class=HTMLResponse)
async def devices_list(request: Request, device_type: str = None, park_id: int = None):
    devices = get_all_devices(device_type, park_id)
    parks = get_parks()
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT name FROM equipment_types ORDER BY name")
    types = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    return templates.TemplateResponse("devices.html", {
        "request": request, "devices": devices, "parks": parks, "types": types,
        "selected_type": device_type, "selected_park": park_id
    })


@router.get("/add", response_class=HTMLResponse)
async def device_add_form(request: Request):
    """Форма добавления нового устройства"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM equipment_types ORDER BY name")
    equipment_types = cursor.fetchall()
    cursor.execute("SELECT id, name FROM parks ORDER BY name")
    parks = cursor.fetchall()
    cursor.execute("SELECT id, name, code FROM track_sections ORDER BY name")
    sections = cursor.fetchall()
    cursor.execute("SELECT id, position_number, position_type FROM brake_positions")
    brake_positions = cursor.fetchall()
    conn.close()

    return templates.TemplateResponse("device_add.html", {
        "request": request,
        "equipment_types": equipment_types,
        "parks": parks,
        "sections": sections,
        "brake_positions": brake_positions
    })


@router.post("/add")
async def device_add(
    equipment_type_id: int = Form(...),
    park_id: int = Form(None),
    track_section_id: int = Form(None),
    brake_position_id: int = Form(None),
    model: str = Form(...),
    inv_number: str = Form(None),
    serial_number: str = Form(None),
    location_detail: str = Form(None),
    install_date: str = Form(None),
    manufacture_date: str = Form(None),
    status: str = Form("active"),
    notes: str = Form("")
):
    """Сохранение нового устройства"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO devices (
                equipment_type_id, park_id, track_section_id, brake_position_id,
                model, inv_number, serial_number, location_detail,
                install_date, manufacture_date, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (equipment_type_id, park_id, track_section_id, brake_position_id,
              model, inv_number, serial_number, location_detail,
              install_date, manufacture_date, status, notes))
        conn.commit()
        device_id = cursor.lastrowid
        
        cursor.execute("SELECT name FROM equipment_types WHERE id = ?", (equipment_type_id,))
        eq_type = cursor.fetchone()
        if eq_type and eq_type[0] == 'Замедлитель':
            cursor.execute("INSERT INTO retarders (device_id, model) VALUES (?, ?)", (device_id, model))
            conn.commit()
        
        if eq_type and eq_type[0] == 'Стрелка':
            cursor.execute("INSERT INTO switches (device_id, switch_number, switch_type) VALUES (?, ?, ?)", 
                          (device_id, model, model))
            conn.commit()
        
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при добавлении: {e}")
    finally:
        conn.close()


# ============= ДИНАМИЧЕСКИЕ МАРШРУТЫ (с параметрами) =============

@router.get("/{device_id}", response_class=HTMLResponse)
async def device_detail(request: Request, device_id: int):
    device = get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    components = get_components(device_id)
    return templates.TemplateResponse("device_detail.html", {
        "request": request, "device": device, "components": components
    })


@router.get("/{device_id}/edit", response_class=HTMLResponse)
async def device_edit_form(request: Request, device_id: int):
    """Форма редактирования устройства"""
    device = get_device_by_id(device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Устройство не найдено")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, icon FROM equipment_types ORDER BY name")
    equipment_types = cursor.fetchall()
    cursor.execute("SELECT id, name FROM parks ORDER BY name")
    parks = cursor.fetchall()
    cursor.execute("SELECT id, name, code FROM track_sections ORDER BY name")
    sections = cursor.fetchall()
    cursor.execute("SELECT id, position_number, position_type FROM brake_positions")
    brake_positions = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse("device_edit.html", {
        "request": request,
        "device": device,
        "equipment_types": equipment_types,
        "parks": parks,
        "sections": sections,
        "brake_positions": brake_positions
    })


@router.post("/{device_id}/edit")
async def device_edit(
    device_id: int,
    equipment_type_id: int = Form(...),
    park_id: int = Form(None),
    track_section_id: int = Form(None),
    brake_position_id: int = Form(None),
    model: str = Form(...),
    inv_number: str = Form(None),
    serial_number: str = Form(None),
    location_detail: str = Form(None),
    install_date: str = Form(None),
    manufacture_date: str = Form(None),
    status: str = Form(...),
    notes: str = Form("")
):
    """Сохранение изменений устройства"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            UPDATE devices SET
                equipment_type_id = ?, park_id = ?, track_section_id = ?, brake_position_id = ?,
                model = ?, inv_number = ?, serial_number = ?, location_detail = ?,
                install_date = ?, manufacture_date = ?, status = ?, notes = ?
            WHERE id = ?
        """, (equipment_type_id, park_id, track_section_id, brake_position_id,
              model, inv_number, serial_number, location_detail,
              install_date, manufacture_date, status, notes, device_id))
        conn.commit()
        
        return RedirectResponse(url=f"/devices/{device_id}", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при обновлении: {e}")
    finally:
        conn.close()


@router.post("/{device_id}/delete")
async def device_delete(device_id: int):
    """Удаление устройства (мягкое)"""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE devices SET status = 'written_off' WHERE id = ?", (device_id,))
        conn.commit()
        return RedirectResponse(url="/devices", status_code=303)
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Ошибка при удалении: {e}")
    finally:
        conn.close()