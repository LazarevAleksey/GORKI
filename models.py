from pydantic import BaseModel
from typing import Optional

class RetarderUpdate(BaseModel):
    model: str
    height_mm: Optional[int] = None
    install_year: Optional[int] = None
    last_repair_year: Optional[int] = None
    total_operations: Optional[int] = None
    planned_repair_year: Optional[int] = None
    residual_value: Optional[float] = None

class SwitchUpdate(BaseModel):
    switch_number: str
    switch_type: str
    rail_type: Optional[str] = None
    has_electric_drive: bool = True
    has_switch_heating: bool = False

class DeviceUpdate(BaseModel):
    model: str
    inv_number: Optional[str] = None
    serial_number: Optional[str] = None
    location_detail: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None