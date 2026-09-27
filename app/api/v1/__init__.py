"""V1 API package."""
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.inventory import router as inventory_router
from app.api.v1.beds import router as beds_router
from app.api.v1.attendance import router as attendance_router

__all__ = ["auth_router", "users_router", "inventory_router", "beds_router", "attendance_router"]
