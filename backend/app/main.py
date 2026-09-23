from uuid import uuid4
from datetime import datetime, timezone
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .ai import fallback_answer, groq_answer
from .config import get_settings
from .database import get_db, init_db
from .knowledge import ROOMS, room_by_id
from .models import Conversation, Memory, Message
from .schemas import *
from .services import search_availability, summarize_context
from .session import anonymous_session

app = FastAPI(title="Hospira AI API", version="2.0.0")
settings = get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/health")
@app.get("/api/v1/health")
async def health():
    return {"status": "ok", "service": "hospira-ai", "mode": "public-demo"}

def uid() -> str:
    return str(uuid4())

async def owned_conversation(db: AsyncSession, conversation_id: str, session_id: str) -> Conversation:
    row = (await db.execute(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == session_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Conversation not found for this demo session")
    return row

@app.get("/api/v1/conversations", response_model=list[ConversationOut])
async def conversations(session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Conversation).where(Conversation.user_id == session_id).order_by(Conversation.updated_at.desc()))).scalars())

@app.post("/api/v1/conversations", response_model=ConversationOut)
async def create_conversation(body: ConversationCreate, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    row = Conversation(id=uid(), user_id=session_id, title=body.title)
    db.add(row); await db.commit(); await db.refresh(row); return row

@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id: str, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    row = await owned_conversation(db, conversation_id, session_id)
    await db.refresh(row, ["messages"])
    return row

@app.patch("/api/v1/conversations/{conversation_id}", response_model=ConversationOut)
async def patch_conversation(conversation_id: str, body: ConversationPatch, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    row = await owned_conversation(db, conversation_id, session_id)
    if body.title is not None: row.title = body.title
    await db.commit(); await db.refresh(row); return row

@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    row = await owned_conversation(db, conversation_id, session_id)
    await db.delete(row); await db.commit(); return {"deleted": True}

@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def chat(body: ChatRequest, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    convo = await owned_conversation(db, body.conversation_id, session_id) if body.conversation_id else Conversation(id=uid(), user_id=session_id, title=body.message[:60])
    if not body.conversation_id: db.add(convo); await db.flush()
    recent_rows = list((await db.execute(select(Message).where(Message.conversation_id == convo.id).order_by(Message.created_at.desc()).limit(8))).scalars())
    recent = [(m.role, m.content) for m in reversed(recent_rows)]
    mems = list((await db.execute(select(Memory).where(Memory.user_id == session_id, Memory.is_active.is_(True)).order_by(Memory.last_referenced_at.desc()).limit(10))).scalars())
    memories = [{"memory_type": m.memory_type, "key": m.key, "value_json": m.value_json} for m in mems]
    result = await groq_answer(body.message, memories, convo.active_room_id, recent, convo.summary)
    if not result.response: result = fallback_answer(body.message, memories, convo.active_room_id, recent)
    now = datetime.now(timezone.utc); convo.active_room_id = result.room_id or convo.active_room_id; convo.active_intent = result.intent; convo.last_message_at = now; convo.updated_at = now
    convo.summary = summarize_context(recent + [("user", body.message), ("assistant", result.response)], result.room_name or (room_by_id(convo.active_room_id) or {}).get("name"))
    db.add(Message(id=uid(), conversation_id=convo.id, user_id=session_id, role="user", content=body.message))
    assistant = Message(id=uid(), conversation_id=convo.id, user_id=session_id, role="assistant", content=result.response, metadata_json=result.model_dump())
    db.add(assistant)
    for candidate in result.memory_candidates:
        existing = (await db.execute(select(Memory).where(Memory.user_id == session_id, Memory.key == candidate["key"], Memory.is_active.is_(True)))).scalar_one_or_none()
        if existing:
            existing.value_json = candidate["value_json"]; existing.confidence = candidate.get("confidence", existing.confidence); existing.last_referenced_at = now
        else:
            db.add(Memory(id=uid(), user_id=session_id, memory_type=candidate["memory_type"], key=candidate["key"], value_json=candidate["value_json"], source_conversation_id=convo.id, confidence=candidate.get("confidence")))
    await db.commit()
    return ChatResponse(conversation_id=convo.id, message_id=assistant.id, assistant_message=result.response, structured=result, referenced_room=room_by_id(result.room_id) if result.room_id else None)

@app.get("/api/v1/memory", response_model=list[MemoryOut])
async def memories(session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    return list((await db.execute(select(Memory).where(Memory.user_id == session_id, Memory.is_active.is_(True)).order_by(Memory.updated_at.desc()))).scalars())

@app.delete("/api/v1/memory/{memory_id}")
async def delete_memory(memory_id: str, session_id=Depends(anonymous_session), db: AsyncSession = Depends(get_db)):
    row = (await db.execute(select(Memory).where(Memory.id == memory_id, Memory.user_id == session_id))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Memory not found")
    row.is_active = False; await db.commit(); return {"deleted": True}

@app.get("/api/v1/rooms")
async def rooms(): return ROOMS
@app.get("/api/v1/rooms/{room_id}")
async def room(room_id: str):
    found = room_by_id(room_id)
    if not found: raise HTTPException(404, "Room not found")
    return found
@app.post("/api/v1/availability/search", response_model=list[AvailabilityResult])
async def availability(body: AvailabilityRequest):
    return search_availability(body.check_in, body.check_out, body.guests, body.room_id)
