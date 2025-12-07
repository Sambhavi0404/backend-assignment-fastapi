import json
import sys
import time
from datetime import datetime

def iso_now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def make_request_log(level: str, request_id: str, method: str, path: str, status: int, latency_ms: float, extra: dict = None):
    payload = {
        "ts": iso_now(),
        "level": level,
        "request_id": request_id,
        "method": method,
        "path": path,
        "status": status,
        "latency_ms": round(latency_ms, 2),
    }
    if extra:
        payload.update(extra)
    line = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
    print(line, file=sys.stdout, flush=True)
