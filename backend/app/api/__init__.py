"""API router — one module per resource, combined here."""
from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.ws_dashboard import router as ws_dashboard_router
from app.api.ws_ingest import router as ws_ingest_router
from app.api.zones import router as zones_router

router = APIRouter()
router.include_router(health_router)
router.include_router(zones_router)
router.include_router(ws_dashboard_router)
router.include_router(ws_ingest_router)
