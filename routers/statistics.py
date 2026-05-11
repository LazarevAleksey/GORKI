from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from database import get_statistics

router = APIRouter(prefix="/statistics", tags=["statistics"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def statistics_page(request: Request):
    stats = get_statistics()
    return templates.TemplateResponse("statistics.html", {"request": request, "stats": stats})