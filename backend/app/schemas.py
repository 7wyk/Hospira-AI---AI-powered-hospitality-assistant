from datetime import date, datetime
from typing import Literal, Any
from pydantic import BaseModel, Field, ConfigDict

class ConversationCreate(BaseModel): title: str = "New chat"
class ConversationPatch(BaseModel): title: str | None = None
class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; title: str; summary: str | None; active_room_id: str | None; active_intent: str | None; created_at: datetime; updated_at: datetime
class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; role: str; content: str; metadata_json: dict | None; created_at: datetime
class ConversationDetail(ConversationOut): messages: list[MessageOut]
class ChatRequest(BaseModel): conversation_id: str | None = None; message: str = Field(min_length=1, max_length=4000)
class AIResponse(BaseModel):
    intent: str; confidence: float = Field(ge=0, le=1); room_id: str | None = None; room_name: str | None = None; guest_count: int | None = None; requires_clarification: bool = False; answer_basis: list[str] = []; response: str; memory_candidates: list[dict[str, Any]] = []
class ChatResponse(BaseModel): conversation_id: str; message_id: str; assistant_message: str; structured: AIResponse; referenced_room: dict | None = None
class MemoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; memory_type: str; key: str; value_json: dict; confidence: float | None; is_active: bool; created_at: datetime
class AvailabilityRequest(BaseModel): check_in: date; check_out: date; guests: int = Field(gt=0, le=20); room_id: str | None = None
class AvailabilityResult(BaseModel): room_id: str; room_name: str; available: bool; capacity: int; price_per_night: float; nights: int; estimated_total: float; reason: str | None = None
