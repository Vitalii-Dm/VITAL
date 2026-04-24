from fastapi import APIRouter

from app.state import world

router = APIRouter()


@router.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "zones": len(world.all_zones())}
