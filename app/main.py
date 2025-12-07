import os
import json
import hmac
import hashlib
import time
import uuid
from typing import Optional

from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, constr, validator

from .config import WEBHOOK_SECRET
from .logging_utils import make_request_log
from . import storage, metrics

app = FastAPI()

class WebhookMessage(BaseModel):
    message_id: constr(strip_whitespace=True, min_length=1)
    from_: constr(strip_whitespace=True, min_length=2) = None
    to: constr(strip_whitespace=True, min_length=2)
    ts: constr(strip_whitespace=True, min_length=1)
    text: Optional[constr(max_length=4096)] = None

    class Config:
        fields = {"from_": "from"}

    @validator("from_")
    def validate_from(cls, v):
        if not (v.startswith("+") and v[1:].isdigit()):
            raise ValueError("from must be E.164-like")
        return v

    @validator("to")
    def validate_to(cls, v):
        if not (v.startswith("+") and v[1:].isdigit()):
            raise ValueError("to must be E.164-like")
        return v

    @validator("ts")
    def validate_ts(cls, v):
        if not v.endswith("Z"):
            raise ValueError("ts must end with Z")
        return v

def compute_signature(secret: str, body_bytes: bytes) -> str:
    return hmac.new(secret.encode(), body_bytes, hashlib.sha256).hexdigest()

@app.middleware("http")
async def log_middleware(request: Request, call_next):
    rid = str(uuid.uuid4())
    start = time.time()
    path = request.url.path

    try:
        response = await call_next(request)
    except Exception as e:
        latency = (time.time() - start) * 1000
        make_request_log("ERROR", rid, request.method, path, 500, latency, {"error": str(e)})
        metrics.inc_http(path, 500)
        metrics.observe_latency(path, latency)
        raise

    latency = (time.time() - start) * 1000
    make_request_log("INFO", rid, request.method, path, response.status_code, latency)
    metrics.inc_http(path, response.status_code)
    metrics.observe_latency(path, latency)

    return response

@app.get("/health/live")
async def live():
    return {"status": "ok"}

@app.get("/health/ready")
async def ready():
    if not WEBHOOK_SECRET:
        return JSONResponse(status_code=503, content={"status": "not ready"})
    try:
        storage.get_conn().execute("SELECT 1")
    except:
        return JSONResponse(status_code=503, content={"status": "not ready"})
    return {"status": "ready"}

@app.post("/webhook")
async def webhook(request: Request, x_signature: Optional[str] = Header(None)):
    body_bytes = await request.body()

    if not x_signature:
        metrics.inc_webhook("invalid_signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    expected = compute_signature(WEBHOOK_SECRET, body_bytes)
    if not hmac.compare_digest(expected, x_signature):
        metrics.inc_webhook("invalid_signature")
        raise HTTPException(status_code=401, detail="invalid signature")

    payload = await request.json()
    try:
        msg = WebhookMessage.parse_obj(payload)
    except Exception as e:
        metrics.inc_webhook("validation_error")
        raise HTTPException(status_code=422, detail=str(e))

    created = storage.insert_message(
        msg.message_id, msg.from_, msg.to, msg.ts, msg.text
    )
    result = "created" if created else "duplicate"
    metrics.inc_webhook(result)

    make_request_log(
        "INFO", str(uuid.uuid4()), "POST", "/webhook", 200, 0.0,
        {"message_id": msg.message_id, "dup": not created, "result": result}
    )

    return {"status": "ok"}

@app.get("/messages")
async def get_messages(limit: int = 50, offset: int = 0, from_: Optional[str] = None, since: Optional[str] = None, q: Optional[str] = None):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)
    data = storage.query_messages(limit, offset, from_, since, q)
    return data

@app.get("/stats")
async def stats():
    return storage.stats_aggregate()

@app.get("/metrics")
async def metrics_endpoint():
    return PlainTextResponse(metrics.metrics_text(), media_type="text/plain")
