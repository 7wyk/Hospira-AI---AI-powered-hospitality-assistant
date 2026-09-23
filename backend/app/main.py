from uuid import uuid4
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from .config import get_settings
from .database import get_db, init_db
from .models import Conversation, Message, Memory
from .schemas import *
from .auth import current_user
from .knowledge import ROOMS, room_by_id
from .ai import grounded_answer

app = FastAPI(title="Hospira AI API", version="1.0.0")
settings=get_settings()
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_list, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
@app.on_event("startup")
async def startup(): await init_db()
@app.get("/health")
async def health(): return {"status":"ok","service":"hospira-ai"}

def uid(): return str(uuid4())
async def owned_conversation(db, conversation_id, user_id):
    row=(await db.execute(select(Conversation).where(Conversation.id==conversation_id, Conversation.user_id==user_id))).scalar_one_or_none()
    if not row: raise HTTPException(404,"Conversation not found")
    return row

@app.get("/api/v1/conversations", response_model=list[ConversationOut])
async def conversations(user=Depends(current_user), db:AsyncSession=Depends(get_db)):
    return list((await db.execute(select(Conversation).where(Conversation.user_id==user["id"]).order_by(Conversation.updated_at.desc()))).scalars())
@app.post("/api/v1/conversations", response_model=ConversationOut)
async def create_conversation(body:ConversationCreate, user=Depends(current_user), db:AsyncSession=Depends(get_db)):
    row=Conversation(id=uid(),user_id=user["id"],title=body.title); db.add(row); await db.commit(); await db.refresh(row); return row
@app.get("/api/v1/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(conversation_id:str,user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    row=await owned_conversation(db,conversation_id,user["id"]); await db.refresh(row,"messages"); return row
@app.patch("/api/v1/conversations/{conversation_id}", response_model=ConversationOut)
async def patch_conversation(conversation_id:str,body:ConversationPatch,user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    row=await owned_conversation(db,conversation_id,user["id"]);
    if body.title is not None: row.title=body.title
    await db.commit(); await db.refresh(row); return row
@app.delete("/api/v1/conversations/{conversation_id}")
async def delete_conversation(conversation_id:str,user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    row=await owned_conversation(db,conversation_id,user["id"]); await db.delete(row); await db.commit(); return {"deleted":True}

@app.post("/api/v1/chat/message", response_model=ChatResponse)
async def chat(body:ChatRequest,user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    if body.conversation_id: convo=await owned_conversation(db,body.conversation_id,user["id"])
    else:
        convo=Conversation(id=uid(),user_id=user["id"],title=body.message[:60]); db.add(convo); await db.flush()
    recent=list((await db.execute(select(Message).where(Message.conversation_id==convo.id).order_by(Message.created_at.desc()).limit(8))).scalars())
    mems=list((await db.execute(select(Memory).where(Memory.user_id==user["id"],Memory.is_active==True).order_by(Memory.last_referenced_at.desc()).limit(10))).scalars())
    mem_dict=[{"memory_type":m.memory_type,"key":m.key,"value_json":m.value_json} for m in mems]
    result=grounded_answer(body.message,mem_dict,convo.active_room_id)
    user_msg=Message(id=uid(),conversation_id=convo.id,user_id=user["id"],role="user",content=body.message); db.add(user_msg)
    assistant_msg=Message(id=uid(),conversation_id=convo.id,user_id=user["id"],role="assistant",content=result.response,metadata_json=result.model_dump()); db.add(assistant_msg)
    convo.active_room_id=result.room_id or convo.active_room_id; convo.active_intent=result.intent; convo.summary=(convo.summary or "") + (" " + body.message[:180])
    if result.memory_candidates:
        candidate=result.memory_candidates[0]; existing=(await db.execute(select(Memory).where(Memory.user_id==user["id"],Memory.key==candidate["key"],Memory.is_active==True))).scalar_one_or_none()
        if not existing: db.add(Memory(id=uid(),user_id=user["id"],memory_type=candidate["memory_type"],key=candidate["key"],value_json=candidate["value_json"],source_conversation_id=convo.id,confidence=candidate["confidence"]))
    await db.commit(); return ChatResponse(conversation_id=convo.id,message_id=assistant_msg.id,assistant_message=result.response,structured=result,referenced_room=room_by_id(result.room_id) if result.room_id else None)

@app.get("/api/v1/memory", response_model=list[MemoryOut])
async def memories(user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    return list((await db.execute(select(Memory).where(Memory.user_id==user["id"],Memory.is_active==True).order_by(Memory.updated_at.desc()))).scalars())
@app.delete("/api/v1/memory/{memory_id}")
async def delete_memory(memory_id:str,user=Depends(current_user),db:AsyncSession=Depends(get_db)):
    row=(await db.execute(select(Memory).where(Memory.id==memory_id,Memory.user_id==user["id"]))).scalar_one_or_none()
    if not row: raise HTTPException(404,"Memory not found")
    row.is_active=False; await db.commit(); return {"deleted":True}
@app.get("/api/v1/rooms")
async def rooms(user=Depends(current_user)): return ROOMS
@app.get("/api/v1/rooms/{room_id}")
async def room(room_id:str,user=Depends(current_user)):
    found=room_by_id(room_id)
    if not found: raise HTTPException(404,"Room not found")
    return found
@app.post("/api/v1/availability/search", response_model=list[AvailabilityResult])
async def availability(body:AvailabilityRequest,user=Depends(current_user)):
    if body.check_out <= body.check_in: raise HTTPException(422,"Check-out must be after check-in")
    nights=(body.check_out-body.check_in).days; candidates=[room_by_id(body.room_id)] if body.room_id else ROOMS
    out=[]
    for r in candidates:
        if not r: continue
        available=r["capacity"]>=body.guests and r["inventory"]>0
        out.append(AvailabilityResult(room_id=r["id"],room_name=r["name"],available=available,capacity=r["capacity"],price_per_night=r["price_per_night"],nights=nights,estimated_total=r["price_per_night"]*nights,reason=None if available else "Capacity or demo inventory is insufficient"))
    return out
