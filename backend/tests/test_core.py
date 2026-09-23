from datetime import date
from fastapi.testclient import TestClient
from app.ai import fallback_answer
from app.main import app
from app.services import search_availability, summarize_context

def test_health():
    response = TestClient(app).get('/api/v1/health')
    assert response.status_code == 200 and response.json()['status'] == 'ok'

def test_unauthorized_protected_route():
    assert TestClient(app).get('/api/v1/conversations').status_code == 401

def test_grounded_premium_room():
    result = fallback_answer('Tell me about the Premium Room', [])
    assert result.room_id == 'premium-room' and 'soaking tub' in result.response

def test_cross_conversation_resolution():
    memories = [{'memory_type': 'room_interest', 'value_json': {'room_id': 'premium-room'}}]
    result = fallback_answer('What is the price for two people?', memories)
    assert result.room_id == 'premium-room' and '$239' in result.response

def test_same_conversation_pronoun_resolution():
    result = fallback_answer('Does it have a bathtub?', [], recent=[('user', 'Tell me about the Premium Room')])
    assert result.room_id == 'premium-room'

def test_safe_unsupported_question():
    result = fallback_answer('What is the capital of France?', [])
    assert result.requires_clarification and 'hotel' in result.response.lower()

def test_summary_is_meaningful():
    summary = summarize_context([('user', 'Tell me about the Premium Room'), ('assistant', 'It has a soaking tub')], 'Premium Room')
    assert 'rooms' in summary and 'Premium Room' in summary

def test_availability_validation_and_total():
    results = search_availability(date(2026, 10, 1), date(2026, 10, 4), 2, 'premium-room')
    assert results[0]['nights'] == 3 and results[0]['estimated_total'] == 717

def test_invalid_availability():
    try:
        search_availability(date(2026, 10, 4), date(2026, 10, 1), 2)
        assert False
    except Exception as error:
        assert 'after' in str(error)
