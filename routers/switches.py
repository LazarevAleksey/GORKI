from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_switches, get_switch_by_id, get_parks

router = APIRouter(prefix="/switches", tags=["switches"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def switches_list(request: Request, park_id: int = None):
    switches = get_switches(park_id)
    parks = get_parks()
    return templates.TemplateResponse("switches.html", {
        "request": request, "switches": switches, "parks": parks, "selected_park": park_id
    })

@router.get("/{switch_id}", response_class=HTMLResponse)
async def switch_detail(request: Request, switch_id: int):
    switch = get_switch_by_id(switch_id)
    if not switch:
        raise HTTPException(status_code=404, detail="Стрелка не найдена")
    return templates.TemplateResponse("switch_detail.html", {
        "request": request, "switch": switch
    })