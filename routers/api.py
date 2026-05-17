import os, json
from fastapi import APIRouter, HTTPException
from database import get_db
from database import get_hierarchy_data, get_statistics, get_retarders, get_switches, get_all_devices


router = APIRouter(prefix="/api", tags=["api"])


DATA_DIR = "data"

# routers/api.py - добавить новый маршрут

@router.get("/ignored-fields")
async def get_ignored_fields():
    """Получить список полей, которые не нужно отображать"""
    ignored_path = os.path.join("data", "ignored_fields.json")
    try:
        with open(ignored_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except FileNotFoundError:
        return {"ignored_fields": ["id", "equipment_id", "device_id", "created_at", "updated_at"], "per_table": {}}


@router.get("/field-labels")
async def get_field_labels():
    """Получить русские названия полей"""
    labels_path = os.path.join(DATA_DIR, "field_labels.json")
    try:
        with open(labels_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("field_labels", {})
    except FileNotFoundError:
        return {}

@router.get("/table-fields/{table_name}")
async def get_table_fields(table_name: str):
    """Получить структуру таблицы для динамического формирования формы"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Проверяем существование таблицы
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail=f"Таблица {table_name} не найдена")
    
    # Получаем структуру таблицы
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    fields = []
    for col in columns:
        # Пропускаем внешние ключи
        if col[1] in ('equipment_id', 'device_id', 'id'):
            continue
        fields.append({
            "name": col[1],
            "type": col[2],
            "nullable": col[3] == 1,
            "default": col[4]
        })
    
    conn.close()
    return {"fields": fields, "table_name": table_name}

# routers/api.py - добавить маршрут

@router.get("/equipment-model-fields")
async def get_equipment_model_fields():
    """Получить структуру таблицы equipment_models для динамической формы"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(equipment_models)")
    columns = cursor.fetchall()
    
    # Поля, которые НЕ показываем в форме
    excluded_fields = ['id', 'type_id', 'created_at', 'manual_file', 'certificate_file']
    
    fields = []
    for col in columns:
        if col[1] in excluded_fields:
            continue
        fields.append({
            "name": col[1],
            "type": col[2],
            "nullable": col[3] == 1,
            "default": col[4]
        })
    
    conn.close()
    return {"fields": fields}

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