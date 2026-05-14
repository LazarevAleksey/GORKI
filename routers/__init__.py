from .retarders import router as retarders_router
from .switches import router as switches_router
from .devices import router as devices_router
from .parks import router as parks_router
from .statistics import router as statistics_router
from .api import router as api_router
from .constructor import router as constructor_router
from .rtu import router as rtu_router

__all__ = [
    'retarders_router', 'switches_router', 'devices_router',
    'parks_router', 'statistics_router', 'api_router',
    'constructor_router', 'rtu_router'
]