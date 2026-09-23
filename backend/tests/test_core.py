from fastapi.testclient import TestClient
from app.main import app
from app.ai import grounded_answer

def test_health():
    assert TestClient(app).get("/health").json()["status"] == "ok"
def test_grounded_premium_room():
    r=grounded_answer("Tell me about the Premium Room",[])
    assert r.room_id == "premium-room" and "soaking tub" in r.response
def test_cross_conversation_resolution():
    memories=[{"memory_type":"room_interest","value_json":{"room_id":"premium-room"}}]
    r=grounded_answer("What is the price for two people?", memories)
    assert r.room_id == "premium-room" and "$239" in r.response
def test_unsupported_is_safe():
    r=grounded_answer("What is the capital of France?",[])
    assert r.requires_clarification and "hotel" in r.response.lower()
