"""Authoritative, versioned knowledge for the fictional demo hotel."""
import json
from pathlib import Path
from typing import Any

_PATH = Path(__file__).resolve().parents[1] / "data" / "hotel_knowledge.json"

def load_knowledge() -> dict[str, Any]:
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    room_ids = [room.get("id") for room in data.get("rooms", [])]
    if len(room_ids) != len(set(room_ids)) or any(not room.get("id") or not room.get("name") or room.get("capacity", 0) < 1 or room.get("price_per_night", 0) < 0 for room in data.get("rooms", [])):
        raise ValueError("Malformed hotel knowledge: rooms require unique IDs, names, capacity, and price")
    if any(not key or not value for key, value in data.get("faqs", {}).items()) or any(not key or not value for key, value in data["property"]["policies"].items()):
        raise ValueError("Malformed hotel knowledge: FAQ and policy keys require answers")
    return data

KNOWLEDGE = load_knowledge()
HOTEL = KNOWLEDGE["property"]
ROOMS = KNOWLEDGE["rooms"]

def room_by_id(room_id: str | None) -> dict[str, Any] | None:
    return next((room for room in ROOMS if room["id"] == room_id), None)

def search_rooms(guests: int = 1) -> list[dict[str, Any]]:
    return [room for room in ROOMS if room["capacity"] >= guests]
