import hashlib
import hmac
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def compute_signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def seed_message(msg_id, ts, text):
    payload = {
        "message_id": msg_id,
        "from": "+111111",
        "to": "+222222",
        "ts": ts,
        "text": text
    }
    body = json.dumps(payload).encode()
    sig = compute_signature(settings.WEBHOOK_SECRET, body)
    client.post(
        "/webhook",
        content=body,
        headers={"X-Signature": sig, "Content-Type": "application/json"}
    )

def test_messages_list():
    # Seed
    seed_message("m_list_1", "2025-01-01T10:00:00Z", "Hello A")
    seed_message("m_list_2", "2025-01-01T11:00:00Z", "Hello B")
    
    response = client.get("/messages")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 2
    assert data["total"] >= 2

def test_messages_filter():
    seed_message("m_filter_1", "2025-01-02T10:00:00Z", "UniqueWord")
    
    response = client.get("/messages?q=UniqueWord")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["data"][0]["text"] == "UniqueWord"
