# routers/constructor.py
from fastapi import APIRouter, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/constructor", tags=["constructor"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def constructor_home(request: Request):
    """Главная страница конструктора"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, class FROM parks ORDER BY name")
    parks = cursor.fetchall()
    
    cursor.execute("SELECT id, name, is_default FROM park_templates ORDER BY is_default DESC, name")
    templates_list = cursor.fetchall()
    
    cursor.execute("SELECT id, name, code FROM section_types")
    section_types = cursor.fetchall()
    
    cursor.execute("SELECT id, name, code FROM zone_types")
    zone_types = cursor.fetchall()
    
    cursor.execute("SELECT id, name, icon FROM equipment_types ORDER BY name")
    equipment_types = cursor.fetchall()
    
    conn.close()
    
    return templates.TemplateResponse("constructor.html", {
        "request": request,
        "parks": parks,
        "templates": templates_list,
        "section_types": section_types,
        "zone_types": zone_types,
        "equipment_types": equipment_types
    })


@router.get("/park/{park_id}")
async def get_park_scheme(park_id: int):
    """Получить JSON схему горки"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT data FROM park_schemes 
        WHERE park_id = ? AND is_active = 1 
        ORDER BY version DESC LIMIT 1
    """, (park_id,))
    row = cursor.fetchone()
    
    if row:
        import json
        scheme = json.loads(row[0])
    else:
        scheme = {"name": None, "sections": []}
    
    conn.close()
    return JSONResponse(content=scheme)


@router.post("/park/{park_id}/save")
async def save_park_scheme(park_id: int, request: Request):
    """Сохранить схему горки"""
    data = await request.json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    import json
    scheme_json = json.dumps(data, ensure_ascii=False)
    
    cursor.execute("UPDATE park_schemes SET is_active = 0 WHERE park_id = ?", (park_id,))
    cursor.execute("""
        INSERT INTO park_schemes (park_id, data, version, is_active)
        VALUES (?, ?, COALESCE((SELECT MAX(version) + 1 FROM park_schemes WHERE park_id = ?), 1), 1)
    """, (park_id, scheme_json, park_id))
    
    conn.commit()
    conn.close()
    
    return JSONResponse(content={"status": "ok"})

@router.get("/templates")
async def get_templates_list():
    """Получить список шаблонов"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, is_default FROM park_templates ORDER BY is_default DESC, name")
    templates = cursor.fetchall()
    conn.close()
    
    return JSONResponse(content=[{"id": t[0], "name": t[1], "is_default": t[2]} for t in templates])

@router.get("/template/{template_id}")
async def get_template(template_id: int):
    """Получить шаблон горки"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT te.*, st.name as section_type_name, zt.name as zone_type_name
        FROM template_elements te
        LEFT JOIN section_types st ON te.section_type_id = st.id
        LEFT JOIN zone_types zt ON te.zone_type_id = zt.id
        WHERE te.template_id = ?
        ORDER BY te.sort_order
    """, (template_id,))
    elements = cursor.fetchall()
    
    result = []
    for elem in elements:
        import json
        result.append({
            "id": elem[0],
            "element_type": elem[2],
            "parent_id": elem[3],
            "section_type_id": elem[4],
            "zone_type_id": elem[5],
            "name": elem[6],
            "code": elem[7],
            "sort_order": elem[8],
            "params": json.loads(elem[9]) if elem[9] else {},
            "section_type_name": elem[11] if len(elem) > 11 else None,
            "zone_type_name": elem[12] if len(elem) > 12 else None
        })
    
    conn.close()
    return JSONResponse(content=result)


@router.post("/template/create")
async def create_template(request: Request):
    """Создать шаблон из текущей схемы"""
    data = await request.json()
    name = data.get("name")
    park_id = data.get("park_id")
    
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO park_templates (name, description) VALUES (?, ?)", (name, f"Создан из горки ID {park_id}"))
    template_id = cursor.lastrowid
    
    cursor.execute("SELECT data FROM park_schemes WHERE park_id = ? AND is_active = 1", (park_id,))
    row = cursor.fetchone()
    
    if row:
        import json
        scheme = json.loads(row[0])
        
        for section in scheme.get("sections", []):
            cursor.execute("""
                INSERT INTO template_elements (template_id, element_type, parent_id, section_type_id, zone_type_id, name, code, sort_order, params)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                template_id, section.get("element_type"), section.get("parent_id"),
                section.get("section_type_id"), section.get("zone_type_id"),
                section.get("name"), section.get("code"), section.get("sort_order"),
                json.dumps(section.get("params", {}))
            ))
    
    conn.commit()
    conn.close()
    
    return JSONResponse(content={"id": template_id, "name": name})


@router.post("/template/{template_id}/apply/{park_id}")
async def apply_template(template_id: int, park_id: int):
    """Применить шаблон к горке"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT element_type, parent_id, section_type_id, zone_type_id, name, code, sort_order, params
        FROM template_elements
        WHERE template_id = ?
        ORDER BY sort_order
    """, (template_id,))
    elements = cursor.fetchall()
    
    import json
    scheme = {"name": None, "sections": []}
    
    for elem in elements:
        scheme["sections"].append({
            "element_type": elem[0],
            "parent_id": elem[1],
            "section_type_id": elem[2],
            "zone_type_id": elem[3],
            "name": elem[4],
            "code": elem[5],
            "sort_order": elem[6],
            "params": json.loads(elem[7]) if elem[7] else {}
        })
    
    cursor.execute("UPDATE park_schemes SET is_active = 0 WHERE park_id = ?", (park_id,))
    cursor.execute("""
        INSERT INTO park_schemes (park_id, data, version, is_active)
        VALUES (?, ?, COALESCE((SELECT MAX(version) + 1 FROM park_schemes WHERE park_id = ?), 1), 1)
    """, (park_id, json.dumps(scheme, ensure_ascii=False), park_id))
    
    conn.commit()
    conn.close()
    
    return JSONResponse(content={"status": "ok"})