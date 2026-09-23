import re, json
from .knowledge import HOTEL, ROOMS, room_by_id, search_rooms
from .schemas import AIResponse

def _resolve(text: str, memories: list[dict], active_room: str | None):
    low = text.lower()
    for r in ROOMS:
        if r["name"].lower() in low or r["id"] in low: return r, 0.98
    if active_room:
        r = room_by_id(active_room)
        if r: return r, 0.95
    room_memories = [m for m in memories if m.get("memory_type") == "room_interest" and m.get("value_json", {}).get("room_id")]
    if len(room_memories) == 1:
        r = room_by_id(room_memories[0]["value_json"]["room_id"]); return r, 0.82 if r else (None, 0)
    return None, 0

def grounded_answer(text: str, memories: list[dict], active_room: str | None = None) -> AIResponse:
    low = text.lower().strip()
    room, confidence = _resolve(text, memories, active_room)
    guest_match = re.search(r"\b(\d+)\s*(?:people|guests?|persons?)\b", low)
    guests = int(guest_match.group(1)) if guest_match else None
    if any(x in low for x in ["forget", "delete my preference", "remove memory"]):
        return AIResponse(intent="memory_delete", confidence=.98, response="You can remove a saved preference from Your Preferences. I will stop using it once it is deleted.", answer_basis=["current_conversation"])
    if any(x in low for x in ["available", "availability", "vacancy"]):
        return AIResponse(intent="availability", confidence=.93, room_id=room["id"] if room else None, room_name=room["name"] if room else None, guest_count=guests, response="I can check demo availability. Please provide your check-in and check-out dates, and I’ll compare rooms by capacity.", answer_basis=["hotel_knowledge","availability_service"])
    if any(x in low for x in ["recommend", "which room", "best room", "suggest"]):
        candidates = search_rooms(guests or 2)
        names = ", ".join(r["name"] for r in candidates[:3])
        return AIResponse(intent="room_recommendation", confidence=.9, guest_count=guests, response=f"For {guests or 2} guest(s), I’d start with {names}. Tell me what matters most—space, quiet, or price—and I can narrow it down.", answer_basis=["hotel_knowledge","room_data"])
    if room and any(x in low for x in ["price", "cost", "rate", "how much"]):
        ref = "You previously asked about the " + room["name"] + ". " if room["name"].lower() not in low else ""
        return AIResponse(intent="room_price", confidence=confidence, room_id=room["id"], room_name=room["name"], guest_count=guests, response=f"{ref}The illustrative rate for the {room['name']} is ${room['price_per_night']} per night for up to {room['capacity']} guests. No booking is made here.", answer_basis=["current_conversation","persistent_memory","hotel_knowledge"], memory_candidates=[{"memory_type":"room_interest","key":room["id"],"value_json":{"room_id":room["id"],"room_name":room["name"]},"confidence":confidence}])
    if room:
        return AIResponse(intent="room_information", confidence=confidence, room_id=room["id"], room_name=room["name"], response=f"The {room['name']} accommodates up to {room['capacity']} guests with {room['beds']}. It includes {', '.join(room['amenities'])} and is priced at ${room['price_per_night']} per night. {room['description']}", answer_basis=["hotel_knowledge","room_data"], memory_candidates=[{"memory_type":"room_interest","key":room["id"],"value_json":{"room_id":room["id"],"room_name":room["name"]},"confidence":confidence}])
    if any(x in low for x in ["check in", "check-in", "check out", "check-out", "breakfast", "pool", "wifi", "wi-fi", "parking", "accessibility", "luggage", "reception", "policy"]):
        snippets=[]
        for key, value in HOTEL.items():
            if key.replace("_","-") in low or key in low: snippets.append(f"{key.replace('_',' ').title()}: {value}")
        if not snippets: snippets=[f"Check-in is at {HOTEL['check_in']} and check-out is at {HOTEL['check_out']}. Reception is open {HOTEL['reception']}."]
        return AIResponse(intent="hotel_information", confidence=.92, response=" ".join(snippets), answer_basis=["hotel_knowledge"])
    return AIResponse(intent="unsupported_or_ambiguous", confidence=.65, requires_clarification=True, response="I can help with Aurelia Hotel rooms, prices, amenities, policies, recommendations, and demo availability. What would you like to know?", answer_basis=["hotel_knowledge"])
