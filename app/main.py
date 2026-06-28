import logging
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.config import settings
from app.database import get_db
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.users import router as users_router
from app.api.v1.endpoints.api_keys import router as api_keys_router
from app.api.v1.endpoints.ingest import router as ingest_router 
from app.api.v1.endpoints.invites import router as invites_router
from app.api.v1.endpoints.dashboards import router as dashboards_router 
from app.api.v1.endpoints.alerts import router as alerts_router
from app.api.v1.endpoints.ws import router as ws_router 
from app.core.exceptions import register_exception_handlers 

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://insights-d176978v7-aniyagniks-projects.vercel.app/"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
register_exception_handlers(app)

# Register routers
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(users_router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(api_keys_router, prefix=f"{settings.API_V1_STR}/api-keys", tags=["API Keys"])
app.include_router(ingest_router, prefix=f"{settings.API_V1_STR}/ingest", tags=["Ingestion"])
app.include_router(invites_router, prefix=f"{settings.API_V1_STR}/invites", tags=["Invitations"])
app.include_router(dashboards_router, prefix=f"{settings.API_V1_STR}/dashboards", tags=["Dashboards"])
app.include_router(alerts_router, prefix=f"{settings.API_V1_STR}/alerts", tags=["Alerts"])
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}/ws", tags=["WebSockets"])

@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    logger.info("Health check endpoint queried")
    db_status = "healthy"
    
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database connection verification failed: {e}")
        db_status = "unhealthy"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "environment": settings.ENVIRONMENT,
        "version": "0.1.0"
    }