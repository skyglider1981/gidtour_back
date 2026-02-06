from .auth import router as auth_router
from .business import router as business_router
from .resources import router as resources_router
from .tours import router as tours_router
from .maps import router as maps_router
from .maps_public import router as maps_public_router
from .upload import router as upload_router
from .schedule_templates import router as schedule_templates_router  # НОВОЕ

all_routers = [
    auth_router,
    business_router,
    resources_router,
    tours_router,
    maps_router,
    maps_public_router,
    upload_router,
    schedule_templates_router,  # НОВОЕ
]