"""Grounded concierge reasoning; Groq is used only after deterministic hotel tools."""
import json
import re
from datetime import date
import httpx
from .config import get_settings
from .knowledge import HOTEL, KNOWLEDGE, ROOMS, room_by_id, search_rooms
from .schemas import AIResponse
from .services import search_availability

def _guests(text, memories):
    match = re.search(r"\b(\d+)\s*(?:adults?|people|guests?|persons?)\b", text.lower())
    if match: return int(match.group(1))
    word_match = re.search(r"\b(one|two|three|four|five|six|seven|eight|nine|ten)\s*(?:adults?|people|guests?|persons?)\b", text.lower())
    if word_match:
        return {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}[word_match.group(1)]
    return next((m.get("value_json", {}).get("guests") for m in memories if m.get("memory_type") == "guest_count"), None)

def _dates(text):
    values = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", text)
    try:
        if len(values) > 1: return date.fromisoformat(values[0]), date.fromisoformat(values[1])
    except ValueError: return None, None
    months = {"jan":1,"january":1,"feb":2,"february":2,"mar":3,"march":3,"apr":4,"april":4,"may":5,"jun":6,"june":6,"jul":7,"july":7,"aug":8,"august":8,"sep":9,"sept":9,"september":9,"oct":10,"october":10,"nov":11,"november":11,"dec":12,"december":12}
    natural = re.findall(r"\b(" + "|".join(months) + r")\.?\s+(\d{1,2})(?:,?\s*(\d{4}))?", text.lower())
    if len(natural) >= 2:
        try:
            first, second = natural[:2]; year = int(first[2] or second[2] or date.today().year)
            return date(year, months[first[0]], int(first[1])), date(int(second[2] or year), months[second[0]], int(second[1]))
        except ValueError: return None, None
    return None, None

def _rooms_in(text, active_room, recent):
    haystack = " ".join([text] + [content for _, content in recent[-6:]]).lower()
    found = [r for r in ROOMS if r["name"].lower() in haystack or r["id"] in haystack]
    if found: return found
    active = room_by_id(active_room)
    return [active] if active and re.search(r"\b(it|that room|this room|the room)\b", text.lower()) else []

def _reply(intent, response, room=None, guests=None, clarification=False, basis=None, memory=None, check_in=None, check_out=None):
    return AIResponse(intent=intent, confidence=.96, response=response, room_id=room["id"] if room else None, room_name=room["name"] if room else None, guest_count=guests, check_in=check_in, check_out=check_out, requires_clarification=clarification, answer_basis=basis or ["hotel_knowledge"], memory_candidates=memory or [])

def _room_memory(room): return [{"memory_type":"room_interest","key":room["id"],"value_json":{"room_id":room["id"],"room_name":room["name"]},"confidence":.96}]
def _fits(guests): return search_rooms(guests)
def _alternatives(guests): return ", ".join(f"{r['name']} (up to {r['capacity']}, ${r['price_per_night']} per night)" for r in _fits(guests)) or "no listed room"

def fallback_answer(text, memories, active_room=None, recent=None):
    recent = recent or []; low = text.lower().strip(); guests = _guests(text, memories); check_in, check_out = _dates(text)
    found = _rooms_in(text, active_room, recent); room = found[0] if found else None
    if not room:
        ids = [m.get("value_json", {}).get("room_id") for m in memories if m.get("memory_type") == "room_interest"]
        room = room_by_id(ids[0]) if len(ids) == 1 else None
    guest_memory = [{"memory_type":"guest_count","key":"guest_count","value_json":{"guests":guests},"confidence":.95}] if guests else []
    if any(x in low for x in ("forget", "delete my preference", "remove memory")):
        return _reply("memory_reference", "You can remove a saved preference from Your Preferences. I will stop using it once it is deleted.", basis=["current_message"])
    if any(x in low for x in ("available", "availability", "vacancy", "next weekend")):
        if not (check_in and check_out and guests):
            missing = []
            if not check_in or not check_out: missing.append("check-in and check-out dates")
            if not guests: missing.append("number of guests")
            return _reply("availability", f"I can check demo availability. Please share your {' and '.join(missing)}.", room, guests, True, ["availability_service"])
        results = search_availability(check_in, check_out, guests, room["id"] if room else None); available = [r for r in results if r["available"]]
        if available:
            listing = "; ".join(f"{r['room_name']} (${r['price_per_night']} per night; ${r['estimated_total']} for {r['nights']} nights)" for r in available)
            answer = f"For {guests} guest(s) from {check_in} to {check_out}, demo availability shows: {listing}. No reservation has been made."
        else: answer = f"I checked demo availability for {guests} guest(s) from {check_in} to {check_out}, but no listed room fits those details."
        return _reply("availability", answer, room, guests, False, ["availability_service", "hotel_knowledge"], guest_memory + (_room_memory(room) if room else []), check_in, check_out)
    if any(x in low for x in ("compare", "difference", " vs ", "versus", "which is cheaper", "the cheaper one", "the other room")):
        compared = found[:2]
        if len(compared) < 2: compared += [r for r in _rooms_in(" ".join(c for _, c in recent), None, []) if r not in compared][:2-len(compared)]
        if len(compared) == 2:
            a, b = compared
            return _reply("room_comparison", f"{a['name']}: up to {a['capacity']} guests, {a['beds']}, ${a['price_per_night']} per night, {', '.join(a['amenities'])}; breakfast {'included' if a['breakfast_included'] else 'not included'}. {b['name']}: up to {b['capacity']} guests, {b['beds']}, ${b['price_per_night']} per night, {', '.join(b['amenities'])}; breakfast {'included' if b['breakfast_included'] else 'not included'}.", a, basis=["hotel_knowledge", "conversation_context"], memory=_room_memory(a))
        return _reply("clarification", "Which two rooms would you like me to compare?", clarification=True)
    if room and any(x in low for x in ("price", "cost", "rate", "how much")):
        if guests and guests > room["capacity"]:
            return _reply("room_price", f"The {room['name']} is ${room['price_per_night']} per night, but it accommodates up to {room['capacity']} guests, so it is not suitable for {guests}. Suitable options are {_alternatives(guests)}.", room, guests, basis=["hotel_knowledge", "room_reasoning"], memory=_room_memory(room)+guest_memory)
        return _reply("room_price", f"The illustrative rate for the {room['name']} is ${room['price_per_night']} per night for up to {room['capacity']} guests.", room, guests, memory=_room_memory(room)+guest_memory)
    if any(x in low for x in ("recommend", "which room", "best room", "suggest", "suitable", "works for", "good for", "cheapest")) or (guests and low.startswith("what about")):
        count = guests or 2; candidates = _fits(count)
        if "cheapest" in low and candidates: candidates = [min(candidates, key=lambda r: r["price_per_night"])]
        if not candidates: return _reply("room_recommendation", f"I do not have a listed room that accommodates {count} guests.", guests=count)
        if "family" in low: candidates.sort(key=lambda r: ("families" not in r["suitable_for"], r["price_per_night"]))
        elif "quiet" in low: candidates.sort(key=lambda r: ("quiet stays" not in r["suitable_for"], r["price_per_night"]))
        names = "; ".join(f"{r['name']} (up to {r['capacity']} guests, ${r['price_per_night']} per night)" for r in candidates[:3])
        return _reply("room_recommendation", f"For {count} guest(s), {names}. {'The lowest-priced fitting option is ' + candidates[0]['name'] + '.' if 'cheapest' in low else ''}", candidates[0], count, basis=["hotel_knowledge", "room_reasoning"], memory=_room_memory(candidates[0])+guest_memory)
    if room and any(x in low for x in ("tell me", "about", "does it", "it have", "amenities", "bathtub", "tub")):
        if any(x in low for x in ("bathtub", "tub")):
            has_tub = any("tub" in item.lower() for item in room["amenities"])
            return _reply("room_information", f"{'Yes' if has_tub else 'No'}, the {room['name']} {'has' if has_tub else 'does not list'} a bathtub. Its listed amenities are {', '.join(room['amenities'])}.", room, memory=_room_memory(room))
        return _reply("room_information", f"The {room['name']} accommodates up to {room['capacity']} guests with {room['beds']}. It includes {', '.join(room['amenities'])}, costs ${room['price_per_night']} per night, and is suited to {', '.join(room['suitable_for'])}. {room['description']}", room, memory=_room_memory(room))
    faq = [("check_in_out", ("check in", "check-in", "check out", "check-out"), f"Check-in is at {HOTEL['check_in']} and check-out is at {HOTEL['check_out']}. Reception is open {HOTEL['reception']}."), ("amenities", ("pool", "swim", "swimming"), HOTEL["pool"]), ("dining_breakfast", ("breakfast",), HOTEL["breakfast"]), ("parking", ("parking",), HOTEL["parking"]), ("accessibility", ("accessible", "accessibility"), HOTEL["accessibility"]), ("hotel_information", ("wifi", "wi-fi", "internet"), HOTEL["wifi"]), ("hotel_information", ("luggage", "bags"), HOTEL["luggage"])]
    for intent, words, answer in faq:
        if any(word in low for word in words): return _reply(intent, answer)
    for key, answer in HOTEL["policies"].items():
        if key.replace("_", " ") in low or (key == "cancellation" and "cancel" in low) or (key == "payment" and any(x in low for x in ("payment", "pay", "card"))): return _reply("policies", answer)
    return _reply("unsupported", "I can help with Aurelia Hotel rooms, prices, amenities, policies, recommendations, and demo availability. What would you like to know?", clarification=True)

async def groq_answer(text, memories, active_room, recent, summary):
    grounded = fallback_answer(text, memories, active_room, recent)
    if grounded.intent != "unsupported": return grounded
    settings = get_settings()
    if not settings.groq_api_key: return grounded
    context = {"message":text,"recent":recent[-8:],"summary":summary,"active_room":active_room,"memories":memories,"knowledge":KNOWLEDGE}
    system = "You are Aurelia Hotel's concierge. Use only supplied hotel data. Never invent hotel facts, capacity, prices, availability, or bookings. Be concise. If data is absent, say it is not specified. Return JSON matching the requested schema."
    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization":f"Bearer {settings.groq_api_key}"}, json={"model":settings.groq_model,"temperature":0.1,"response_format":{"type":"json_object"},"messages":[{"role":"system","content":system},{"role":"user","content":json.dumps(context, default=str)}]})
            response.raise_for_status(); result = AIResponse.model_validate_json(response.json()["choices"][0]["message"]["content"])
            if result.room_id and not room_by_id(result.room_id): return grounded
            if result.room_id: result.room_name = room_by_id(result.room_id)["name"]
            return result if result.response else grounded
    except (httpx.HTTPError, KeyError, TypeError, ValueError): return grounded
