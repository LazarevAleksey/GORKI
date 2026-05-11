from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from database import get_retarders, get_retarder_by_id, update_retarder, get_parks
from models import RetarderUpdate

router = APIRouter(prefix="/retarders", tags=["retarders"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def retarders_list(request: Request, park_id: int = None, position: str = None):
    retarders = get_retarders(park_id, position)
    parks = get_parks()
    return templates.TemplateResponse("retarders.html", {
        "request": request, "retarders": retarders,
        "parks": parks, "selected_park": park_id, "selected_position": position
    })

@router.get("/{retarder_id}", response_class=HTMLResponse)
async def retarder_detail(request: Request, retarder_id: int):
    retarder = get_retarder_by_id(retarder_id)
    if not retarder:
        raise HTTPException(status_code=404, detail="Замедлитель не найден")
    return templates.TemplateResponse("retarder_detail.html", {
        "request": request, "retarder": retarder
    })

@router.post("/{retarder_id}/edit")
async def retarder_edit(
    retarder_id: int,
    model: str = Form(...),
    height_mm: int = Form(None),
    install_year: int = Form(None),
    last_repair_year: int = Form(None),
    total_operations: int = Form(None),
    planned_repair_year: int = Form(None),
    residual_value: float = Form(None)
):
    data = RetarderUpdate(
        model=model, height_mm=height_mm, install_year=install_year,
        last_repair_year=last_repair_year, total_operations=total_operations,
        planned_repair_year=planned_repair_year, residual_value=residual_value
    )
    update_retarder(retarder_id, data)
    return RedirectResponse(url=f"/retarders/{retarder_id}", status_code=303)