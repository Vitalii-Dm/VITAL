"""FastAPI application factory.

Keeps three responsibilities only:
  1. wire the API router
  2. configure CORS
  3. start / stop background tasks (CSI UDP listener + fusion loop)

Everything else (signal processing, fusion, alerts) lives in its own
module tree and is covered by unit tests.
"""
from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.config import settings
from app.fusion.loop import fusion_loop
from app.ingest.csi_udp import run_udp_listener
from app.ingest.handlers import on_csi_frame
from app.logging_setup import configure_logging

configure_logging()
log = logging.getLogger("vital")


@asynccontextmanager
async def lifespan(app: FastAPI):
    udp_transport = await run_udp_listener(
        settings.csi_udp_host, settings.csi_udp_port, on_csi_frame
    )
    fusion_task = asyncio.create_task(fusion_loop(), name="fusion-loop")
    log.info("VITAL backend up — CORS=%s", settings.cors_origin_list)
    try:
        yield
    finally:
        fusion_task.cancel()
        udp_transport.close()
        try:
            await fusion_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="VITAL", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
app.include_router(api_router)
