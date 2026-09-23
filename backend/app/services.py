from datetime import date
from fastapi import HTTPException
from .knowledge import ROOMS, room_by_id


def summarize_context(messages: list[tuple[str, str]], room_name: str | None = None) -> str:
    user_text = " ".join(content for role, content in messages if role == "user")[-600:]
    topics = []
    lowered = user_text.lower()
    for label, terms in (("rooms", ("room", "suite")), ("pricing", ("price", "cost", "rate")), ("amenities", ("pool", "breakfast", "wifi", "parking")), ("availability", ("available", "availability", "date"))):
        if any(term in lowered for term in terms): topics.append(label)
    topic_text = ", ".join(topics) or "hotel information"
    room_text = f" The latest room discussed was {room_name}." if room_name else ""
    return f"Guest is discussing {topic_text}. Recent user context: {user_text}.{room_text}"[:1000]


def search_availability(check_in: date, check_out: date, guests: int, room_id: str | None = None) -> list[dict]:
    if check_out <= check_in:
        raise HTTPException(status_code=422, detail="Check-out must be after check-in")
    if guests <= 0:
        raise HTTPException(status_code=422, detail="Guest count must be positive")
    nights = (check_out - check_in).days
    candidates = [room_by_id(room_id)] if room_id else ROOMS
    results = []
    for room in candidates:
        if not room:
            continue
        available = room["capacity"] >= guests and room["inventory"] > 0
        results.append({"room_id": room["id"], "room_name": room["name"], "available": available, "capacity": room["capacity"], "price_per_night": room["price_per_night"], "nights": nights, "estimated_total": room["price_per_night"] * nights, "reason": None if available else "Capacity or demo inventory is insufficient"})
    return results
