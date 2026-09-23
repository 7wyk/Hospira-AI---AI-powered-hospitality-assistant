import json
import re
import httpx
from .config import get_settings
from .knowledge import HOTEL, ROOMS, room_by_id, search_rooms
from .schemas import AIResponse


def resolve_room(text: str, memories: list[dict], active_room: str | None, recent: list[tuple[str, str]]) -> tuple[dict | None, float]:
    haystack = " ".join([text, active_room or ""] + [content for _, content in recent[-6:]]).lower()
    for room in ROOMS:
        if room["name"].lower() in haystack or room["id"] in haystack:
            return room, 0.98
    room_memories = [m for m in memories if m.get("memory_type") == "room_interest" and m.get("value_json", {}).get("room_id")]
    if len(room_memories) == 1:
        room = room_by_id(room_memories[0]["value_json"]["room_id"])
        return (room, 0.86) if room else (None, 0)
    return None, 0


def fallback_answer(text: str, memories: list[dict], active_room: str | None = None, recent: list[tuple[str, str]] | None = None) -> AIResponse:
    recent = recent or []
    low = text.lower().strip()
    room, confidence = resolve_room(text, memories, active_room, recent)
    match = re.search(r"\b(\d+)\s*(?:people|guests?|persons?)\b", low)
    guests = int(match.group(1)) if match else None
    if any(x in low for x in ("forget", "delete my preference", "remove memory")):
        return AIResponse(intent="memory_delete", confidence=.98, response="You can remove a saved preference from Your Preferences. I will stop using it once it is deleted.", answer_basis=["current_message"])
    if any(x in low for x in ("available", "availability", "vacancy")):
        return AIResponse(intent="availability", confidence=.93, room_id=room["id"] if room else None, room_name=room["name"] if room else None, guest_count=guests, response="I can check demo availability. Please provide your check-in and check-out dates, and I’ll compare rooms by capacity.", answer_basis=["hotel_knowledge", "availability_service"])
    if any(x in low for x in ("recommend", "which room", "best room", "suggest")):
        candidates = search_rooms(guests or 2)
        return AIResponse(intent="room_recommendation", confidence=.9, guest_count=guests, response=f"For {guests or 2} guest(s), I’d start with {', '.join(r['name'] for r in candidates[:3])}. Tell me whether space, quiet, or price matters most.", answer_basis=["hotel_knowledge", "room_data"])
    if room and any(x in low for x in ("price", "cost", "rate", "how much")):
        ref = "You previously asked about the " + room["name"] + ". " if room["name"].lower() not in low else ""
        return AIResponse(intent="room_price", confidence=confidence, room_id=room["id"], room_name=room["name"], guest_count=guests, response=f"{ref}The illustrative rate for the {room['name']} is ${room['price_per_night']} per night for up to {room['capacity']} guests. No booking is made here.", answer_basis=["conversation_context", "persistent_memory", "hotel_knowledge"], memory_candidates=[{"memory_type":"room_interest", "key":room["id"], "value_json":{"room_id":room["id"], "room_name":room["name"]}, "confidence":confidence}])
    if room and any(x in low for x in ("does it", "it have", "amenities", "tell me", "about")):
        return AIResponse(intent="room_information", confidence=confidence, room_id=room["id"], room_name=room["name"], response=f"The {room['name']} accommodates up to {room['capacity']} guests with {room['beds']}. It includes {', '.join(room['amenities'])} and is priced at ${room['price_per_night']} per night. {room['description']}", answer_basis=["conversation_context", "hotel_knowledge"], memory_candidates=[{"memory_type":"room_interest", "key":room["id"], "value_json":{"room_id":room["id"], "room_name":room["name"]}, "confidence":confidence}])
    if any(x in low for x in ("check in", "check-in", "check out", "check-out", "breakfast", "pool", "wifi", "wi-fi", "parking", "accessibility", "luggage", "reception", "policy")):
        if "breakfast" in low: answer = HOTEL["breakfast"]
        elif "pool" in low: answer = HOTEL["pool"]
        elif "wifi" in low or "wi-fi" in low: answer = HOTEL["wifi"]
        elif "parking" in low: answer = HOTEL["parking"]
        elif "accessibility" in low: answer = HOTEL["accessibility"]
        elif "luggage" in low: answer = HOTEL["luggage"]
        else: answer = f"Check-in is at {HOTEL['check_in']}, check-out is at {HOTEL['check_out']}, and reception is open {HOTEL['reception']}."
        return AIResponse(intent="hotel_information", confidence=.92, response=answer, answer_basis=["hotel_knowledge"])
    return AIResponse(intent="unsupported_or_ambiguous", confidence=.65, requires_clarification=True, response="I can help with Aurelia Hotel rooms, prices, amenities, policies, recommendations, and demo availability. What would you like to know?", answer_basis=["hotel_knowledge"])


async def groq_answer(text: str, memories: list[dict], active_room: str | None, recent: list[tuple[str, str]], summary: str | None) -> AIResponse:
    settings = get_settings()
    if not settings.groq_api_key:
        return fallback_answer(text, memories, active_room, recent)
    rooms_json = json.dumps(ROOMS, separators=(",", ":"))
    context = {"current_message": text, "recent_messages": recent[-8:], "summary": summary, "active_room": active_room, "memories": memories, "hotel": HOTEL, "rooms": ROOMS}
    system = f"You are Hospira AI for Aurelia Hotel. Use only the supplied hotel data. Never invent prices, capacity, availability, or bookings. Return JSON only with keys intent, confidence, room_id, room_name, guest_count, requires_clarification, answer_basis, memory_candidates, response. Factual room values must be copied from this data: {rooms_json}. If uncertain, clarify. Context: {json.dumps(context, default=str)}"
    body = {"model": settings.groq_model, "temperature": 0.1, "response_format": {"type": "json_object"}, "messages": [{"role": "system", "content": system}, {"role": "user", "content": text}]}
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization": f"Bearer {settings.groq_api_key}"}, json=body)
            response.raise_for_status()
            parsed = response.json()["choices"][0]["message"]["content"]
            result = AIResponse.model_validate_json(parsed)
            # Backend owns facts: replace model-selected room facts with KB facts.
            if result.room_id:
                room = room_by_id(result.room_id)
                if not room:
                    return fallback_answer(text, memories, active_room, recent)
            return result
    except (httpx.HTTPError, KeyError, TypeError, ValueError):
        return fallback_answer(text, memories, active_room, recent)
