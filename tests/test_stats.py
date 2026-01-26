import json
import hashlib
import hmac
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings

client = TestClient(app)

def compute_signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

def seed_message_from(msg_id, from_num):
    payload = {
        "message_id": msg_id,
        "from": from_num,
        "to": "+222222",
        "ts": "2025-01-03T10:00:00Z",
        "text": "Hi"
    }
    body = json.dumps(payload).encode()
    sig = compute_signature(settings.WEBHOOK_SECRET, body)
    client.post(
        "/webhook",
        content=body,
        headers={"X-Signature": sig, "Content-Type": "application/json"}
    )

def test_stats():
    seed_message_from("m_stats_1", "+999999999")
    seed_message_from("m_stats_2", "+999999999")
    seed_message_from("m_stats_3", "+888888888")
    
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_messages"] >= 3
    # Check if our sender is in the list
    found = False
    for sender in data["messages_per_sender"]:
        if sender["from"] == "+999999999":
            assert sender["count"] >= 2
            found = True
    assert found
