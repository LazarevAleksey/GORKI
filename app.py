from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from routers import (
    retarders_router, switches_router, devices_router,
    parks_router, statistics_router, api_router, constructor_router, rtu_router
)


app = FastAPI(title="Учёт оборудования сортировочной горки")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
app.state.templates = templates

# Подключаем роутеры
app.include_router(retarders_router)
app.include_router(switches_router)
app.include_router(devices_router)
app.include_router(parks_router)
app.include_router(statistics_router)
app.include_router(api_router)
# Подключить роутер
app.include_router(constructor_router)
app.include_router(rtu_router)

@app.get("/")
async def home(request: Request):
    from database import get_statistics, get_parks
    stats = get_statistics()
    parks = get_parks()
    return templates.TemplateResponse("index.html", {
        "request": request, "stats": stats, "parks": parks
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)