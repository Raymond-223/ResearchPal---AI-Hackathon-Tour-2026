from __future__ import annotations
import time
import uuid
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origins] if settings.cors_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    start = time.time()
    try:
        response = await call_next(request)
        return response
    finally:
        cost_ms = int((time.time() - start) * 1000)
        status = getattr(locals().get("response", None), "status_code", "NA")
        logging.info(
            f"rid={request_id} {request.method} {request.url.path} status={status} cost_ms={cost_ms}"
        )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response

@app.get("/health")
async def health():
    return {"ok": True, "name": settings.app_name}

app.include_router(router, prefix="/api")