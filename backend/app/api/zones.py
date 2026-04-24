from fastapi import APIRouter

from app.state import world

router = APIRouter()


@router.get("/api/zones")
async def zones() -> list[dict]:
    out: list[dict] = []
    for z in world.all_zones():
        f = z.last_fusion
        out.append(
            {
                "zone": z.zone_id,
                "bpm": round(z.last_bpm, 1),
                "temp_c": round(z.last_temp_c, 1),
                "rh_pct": round(z.last_rh_pct, 1),
                "severity": f.severity.value if f else "low",
                "event": f.event.value if f else "normal",
                "updated_at": z.updated_at,
            }
        )
    return out
