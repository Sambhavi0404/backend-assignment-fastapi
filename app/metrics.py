import threading
import time

_lock = threading.Lock()
_counters = {
    "http_requests_total": {},
    "webhook_requests_total": {},
}
_latency_buckets = [100, 500, 1000]
_latency_data = {
    "request_latency_ms_bucket": {},
    "request_latency_ms_count": {},
    "request_latency_ms_sum": {},
}

def inc_http(path: str, status: int):
    with _lock:
        key = (path, str(status))
        _counters["http_requests_total"][key] = _counters["http_requests_total"].get(key, 0) + 1

def inc_webhook(result: str):
    with _lock:
        _counters["webhook_requests_total"][result] = _counters["webhook_requests_total"].get(result, 0) + 1

def observe_latency(path: str, latency_ms: float):
    with _lock:
        for b in _latency_buckets:
            key = (path, str(b))
            _latency_data["request_latency_ms_bucket"][key] = _latency_data["request_latency_ms_bucket"].get(key, 0) + (1 if latency_ms <= b else 0)
        key_inf = (path, "+Inf")
        _latency_data["request_latency_ms_bucket"][key_inf] = _latency_data["request_latency_ms_bucket"].get(key_inf, 0) + 1

        _latency_data["request_latency_ms_count"][path] = _latency_data["request_latency_ms_count"].get(path, 0) + 1
        _latency_data["request_latency_ms_sum"][path] = _latency_data["request_latency_ms_sum"].get(path, 0.0) + latency_ms

def metrics_text():
    lines = []
    with _lock:
        for (path, status), val in _counters["http_requests_total"].items():
            lines.append(f'http_requests_total{{path="{path}",status="{status}"}} {val}')
        for result, val in _counters["webhook_requests_total"].items():
            lines.append(f'webhook_requests_total{{result="{result}"}} {val}')
        for (path, le), val in _latency_data["request_latency_ms_bucket"].items():
            lines.append(f'request_latency_ms_bucket{{path="{path}",le="{le}"}} {val}')
        for path, val in _latency_data["request_latency_ms_count"].items():
            lines.append(f'request_latency_ms_count{{path="{path}"}} {val}')
        for path, val in _latency_data["request_latency_ms_sum"].items():
            lines.append(f'request_latency_ms_sum{{path="{path}"}} {round(val,2)}')
    return "\n".join(lines) + "\n"
