from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session
from app.services.memory import (
    short_append, short_context, ensure_conversation, persist_message,
    add_user_memory, semantic_retrieve_user_memory, join_context
)
from app.providers.gemini import generate_with_gemini

router = APIRouter()

class ChatIn(BaseModel):
    user_id: str
    prompt: str

class ChatOut(BaseModel):
    reply: str
    provider: str

@router.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn, session: AsyncSession = Depends(get_session)):
    prompt = body.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    # Short-term memory (in RAM)
    short_append(body.user_id, "user", prompt)

    # Ensure conversation & persist user message
    conv = await ensure_conversation(session, body.user_id)
    await persist_message(session, conv.id, body.user_id, "user", prompt)

    # Retrieve contexts
    short_ctx = short_context(body.user_id, limit=10)
    long_ctx = await semantic_retrieve_user_memory(session, body.user_id, query=prompt)

    memory_block = join_context(short_ctx, long_ctx)

    # ✅ Direct Gemini call instead of CrewAI
    reply = await generate_with_gemini(
        f"{memory_block}\n\nUser: {prompt}\nAssistant:"
    )

    # Persist assistant reply
    await persist_message(session, conv.id, body.user_id, "assistant", reply)

    # Heuristic: promote key facts to long-term memory
    if len(prompt) < 200 and any(x in prompt.lower() for x in ["i like", "my name", "remind", "preference", "birthday"]):
        await add_user_memory(session, body.user_id, text=prompt, kind="preference")

    await session.commit()

    from app.settings import settings
    return ChatOut(reply=reply, provider=settings.AI_PROVIDER)
