from datetime import date
import pytest
from fastapi.testclient import TestClient
from app.ai import fallback_answer
from app.main import app
from app.services import search_availability, summarize_context
from app.knowledge import HOTEL, ROOMS

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client

def headers(session: str = "browser-session-a-123456"):
    return {"X-Anonymous-Session": session}

def test_health_is_public(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200 and response.json()['mode'] == 'public-demo'

def test_conversation_list_is_public_with_anonymous_scope(client):
    response = client.get('/api/v1/conversations', headers=headers())
    assert response.status_code == 200

def test_anonymous_sessions_are_isolated(client):
    first = client.post('/api/v1/conversations', headers=headers('browser-a-123456'), json={'title': 'A session'})
    assert first.status_code == 200
    conversation_id = first.json()['id']
    other = client.get(f'/api/v1/conversations/{conversation_id}', headers=headers('browser-b-123456'))
    assert other.status_code == 404

def test_public_chat_persists_with_session_scope(client):
    response = client.post('/api/v1/chat/message', headers=headers('chat-session-123456'), json={'message': 'Tell me about the Premium Room'})
    assert response.status_code == 200
    assert response.json()['structured']['room_id'] == 'premium-room'

def test_availability_is_public(client):
    response = client.post('/api/v1/availability/search', json={'check_in': '2026-10-01', 'check_out': '2026-10-04', 'guests': 2})
    assert response.status_code == 200

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

def test_check_in_and_pool_are_grounded():
    assert '3:00 PM' in fallback_answer('What time is check-in?', []).response
    pool = fallback_answer('Does the hotel have a swimming pool?', []).response
    assert 'Yes' in pool and '6:00 AM' in pool and '10:00 PM' in pool

def test_three_guest_reasoning_excludes_two_person_rooms():
    result = fallback_answer('Which room is suitable for three guests?', [])
    assert 'Family Room' in result.response and 'Aurelia Suite' in result.response
    assert 'Standard Room' not in result.response and 'Premium Room' not in result.response

def test_price_respects_requested_occupancy():
    result = fallback_answer('price for 3 guests in standard room?', [])
    assert 'not suitable for 3' in result.response and 'Family Room' in result.response

def test_breakfast_and_cancellation_are_from_knowledge():
    assert 'Aurelia Suite' in fallback_answer('Is breakfast included?', []).response
    assert HOTEL['policies']['cancellation'] == fallback_answer('What is the cancellation policy?', []).response

def test_chat_availability_executes_tool():
    result = fallback_answer('Do you have rooms available for 2 guests from 2026-10-01 to 2026-10-04?', [])
    assert result.intent == 'availability' and 'demo availability shows' in result.response

def test_follow_up_recalculates_capacity():
    first = fallback_answer('Which room is best for 2 people?', [])
    second = fallback_answer('What about 3 people?', [], first.room_id, [('user', 'Which room is best for 2 people?')])
    assert second.intent == 'room_recommendation' and 'Standard Room' not in second.response

def test_family_request_ignores_stale_guest_memory_and_short_follow_up_reasons():
    family = fallback_answer('Which room is best for a family?', [{'memory_type': 'guest_count', 'value_json': {'guests': 1}}])
    assert family.guest_count == 4 and 'Family Room' in family.response and 'Standard Room' not in family.response
    follow_up = fallback_answer('for 4 guests?', [], family.room_id, [('user', 'Which room is best for a family?')])
    assert follow_up.intent == 'room_recommendation' and follow_up.guest_count == 4 and 'Family Room' in follow_up.response

def test_comparison_uses_known_attributes():
    result = fallback_answer('Compare Premium and Deluxe.', [])
    assert result.intent == 'room_comparison' and 'Premium Room' in result.response and 'Deluxe Room' in result.response

def test_knowledge_has_required_stable_data():
    assert len({r['id'] for r in ROOMS}) == len(ROOMS)
    assert all(r['id'] and r['name'] and r['capacity'] > 0 and r['price_per_night'] >= 0 for r in ROOMS)
    assert all(key and answer for key, answer in HOTEL['policies'].items())
