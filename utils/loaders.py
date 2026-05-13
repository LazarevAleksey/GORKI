import json
import os

DATA_DIR = "data"

def load_retarder_models():
    with open(os.path.join(DATA_DIR, "retarder_models.json"), "r", encoding="utf-8") as f:
        return json.load(f)["models"]

def load_switch_models():
    with open(os.path.join(DATA_DIR, "switch_models.json"), "r", encoding="utf-8") as f:
        return json.load(f)["models"]

def load_equipment_types():
    with open(os.path.join(DATA_DIR, "equipment_types.json"), "r", encoding="utf-8") as f:
        return json.load(f)["types"]
    
def get_retarder_model_by_id(model_id):
    """Получить модель замедлителя по ID"""
    models = load_retarder_models()
    for model in models:
        if model["id"] == model_id:
            return model
    return None

def get_switch_model_by_id(model_id):
    """Получить модель стрелки по ID"""
    models = load_switch_models()
    for model in models:
        if model["id"] == model_id:
            return model
    return None