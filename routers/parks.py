from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_parks, get_park_by_id, get_track_sections, get_brake_positions

router = APIRouter(prefix="/parks", tags=["parks"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def parks_list(request: Request):
    parks = get_parks()
    for park in parks:
        sections = get_track_sections(park['id'])
        park['sections_count'] = len(sections)
    return templates.TemplateResponse("parks.html", {"request": request, "parks": parks})

@router.get("/{park_id}", response_class=HTMLResponse)
async def park_detail(request: Request, park_id: int):
    park = get_park_by_id(park_id)
    if not park:
        raise HTTPException(status_code=404, detail="Горка не найдена")
    sections = get_track_sections(park_id)
    brake_positions = get_brake_positions()
    return templates.TemplateResponse("park_detail.html", {
        "request": request, "park": park, "sections": sections, "brake_positions": brake_positions
    })