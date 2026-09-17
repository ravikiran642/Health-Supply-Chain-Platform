from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.api.v1.auth import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Multi-tenant health supply chain backend for India with role-based access control, geographic scoping, JWT authentication, and audit logging.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# CORS Middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Auth router under both /auth and /api/v1/auth for specification consistency
app.include_router(auth_router, prefix="")
app.include_router(auth_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["System"])
def health_check():
    """Liveness probe for orchestration and container health monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT
    }


def custom_openapi():
    """Configure OpenAPI docs with standard JWT Bearer authorization scheme."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Inject Bearer Auth Security Scheme
    openapi_schema["components"] = openapi_schema.get("components", {})
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT Bearer token in the format: Bearer <token>"
        }
    }

    # Apply Bearer scheme to protected paths
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if method in ["get", "post", "put", "delete", "patch"]:
                # Public routes don't require authorization
                if path in ["/auth/login", "/auth/refresh", "/api/v1/auth/login", "/api/v1/auth/refresh", "/health"]:
                    continue
                operation["security"] = [{"HTTPBearer": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi  # type: ignore[method-assign]
