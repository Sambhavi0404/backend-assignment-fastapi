import os
import json
import hmac
import hashlib
from fastapi.testclient import TestClient

os.environ["WEBHOOK_SECRET"] = "testsecret"
from app.main import app
from app.config import WEBHOOK_SECRET

client = TestClient(app)

def compute_sig(body: bytes):
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

def test_messages():
    msgs = [
        {"message_id":"x1","from":"+911111111111","to":"+1415","ts":"2025-01-15T09:00:00Z","text":"Earlier"},
        {"message_id":"x2","from":"+922222222222","to":"+1415","ts":"2025-01-15T11:00:00Z","text":"Later"},
    ]
    for m in msgs:
        b = json.dumps(m).encode()
        sig = compute_sig(b)
        client.post("/webhook", data=b, headers={"Content-Type":"application/json","X-Signature":sig})

    r = client.get("/messages")
    assert r.status_code == 200
    assert "data" in r.json()
