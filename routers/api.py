from fastapi import APIRouter
from database import get_hierarchy_data, get_statistics, get_retarders, get_switches, get_all_devices

router = APIRouter(prefix="/api", tags=["api"])

@router.get("/hierarchy")
async def get_hierarchy():
    return get_hierarchy_data()

@router.get("/statistics")
async def get_stats():
    return get_statistics()

@router.get("/retarders")
async def api_retarders(park_id: int = None):
    return get_retarders(park_id)

@router.get("/switches")
async def api_switches(park_id: int = None):
    return get_switches(park_id)

@router.get("/devices")
async def api_devices(device_type: str = None, park_id: int = None):
    return get_all_devices(device_type, park_id)