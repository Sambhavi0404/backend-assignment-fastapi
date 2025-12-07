from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_stats():
    r = client.get("/stats")
    assert r.status_code == 200
    j = r.json()
    assert "total_messages" in j
    assert "senders_count" in j
