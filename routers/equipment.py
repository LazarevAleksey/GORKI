from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_db

router = APIRouter(prefix="/equipment", tags=["equipment"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def equipment_list(request: Request):
    """Список оборудования"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.*, p.name as park_name
        FROM retarders r
        LEFT JOIN parks p ON r.park_id = p.id
        ORDER BY p.name, r.model
    """)
    equipment = cursor.fetchall()
    conn.close()
    
    return templates.TemplateResponse(
        "equipment.html", 
        {"request": request, "equipment": equipment}
    )