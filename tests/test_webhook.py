import os
import json
import hmac
import hashlib
import tempfile

import pytest
from fastapi.testclient import TestClient

os.environ["WEBHOOK_SECRET"] = "testsecret"
tmpdb = tempfile.gettempdir() + "/test_app.db"
os.environ["DATABASE_URL"] = f"sqlite:///{tmpdb}"

from app.main import app
from app.config import WEBHOOK_SECRET

client = TestClient(app)

def compute_sig(body: bytes):
    return hmac.new(WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

def test_invalid_signature():
    body = json.dumps({"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"})
    r = client.post("/webhook", data=body, headers={"Content-Type":"application/json", "X-Signature":"123"})
    assert r.status_code == 401

def test_valid_insert_and_idempotent():
    body_dict = {"message_id":"m1","from":"+919876543210","to":"+14155550100","ts":"2025-01-15T10:00:00Z","text":"Hello"}
    body = json.dumps(body_dict).encode()
    sig = compute_sig(body)

    r1 = client.post("/webhook", data=body, headers={"Content-Type":"application/json","X-Signature":sig})
    assert r1.status_code == 200

    r2 = client.post("/webhook", data=body, headers={"Content-Type":"application/json","X-Signature":sig})
    assert r2.status_code == 200
