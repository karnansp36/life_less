from collections import defaultdict, deque
from typing import Deque, Tuple, List
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text as sql_text
from app.settings import settings
from app.models.conversation import Conversation, Message, UserMemory
from app.services.embeddings import embed_text

# ------- Short-term in-memory (fast) -------
# user_id -> deque[(role, content)]
_SHORT_MEMORY: dict[str, Deque[Tuple[str, str]]] = defaultdict(lambda: deque(maxlen=settings.SHORT_MEMORY_MAXLEN))

def short_append(user_id: str, role: str, content: str):
    _SHORT_MEMORY[user_id].append((role, content))

def short_context(user_id: str, limit: int = 10) -> str:
    msgs = list(_SHORT_MEMORY[user_id])[-limit:]
    lines: List[str] = []
    for role, content in msgs:
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    return "\n".join(lines) if lines else "(no prior messages)"

# ------- DB persistence -------
async def ensure_conversation(session: AsyncSession, user_id: str) -> Conversation:
    q = select(Conversation).where(Conversation.user_id == user_id).order_by(Conversation.created_at.asc())
    res = await session.execute(q)
    conv = res.scalars().first()
    if conv:
        return conv
    conv = Conversation(user_id=user_id, title=None)
    session.add(conv)
    await session.flush()
    return conv

async def persist_message(session: AsyncSession, conversation_id: int, user_id: str, role: str, content: str):
    msg = Message(conversation_id=conversation_id, user_id=user_id, role=role, content=content)
    session.add(msg)
    await session.flush()

# ------- Long-term memory (RAG over personal data) -------
async def add_user_memory(session: AsyncSession, user_id: str, text: str, kind: str = "fact"):
    vec = embed_text(text)
    stmt = insert(UserMemory).values(user_id=user_id, text=text, kind=kind, embedding=vec)
    await session.execute(stmt)

async def semantic_retrieve_user_memory(session: AsyncSession, user_id: str, query: str, top_k: int | None = None) -> list[UserMemory]:
    top_k = top_k or settings.RAG_TOP_K
    qvec = embed_text(query)
    # pgvector cosine distance: <-> operator for euclidean; use cosine_distance for cosine
    sql = sql_text("""
        SELECT id, user_id, kind, text, embedding, created_at
        FROM user_memory
        WHERE user_id = :uid
        ORDER BY embedding <#> :qvec   -- cosine distance
        LIMIT :k
    """)
    res = await session.execute(sql, {"uid": user_id, "qvec": qvec, "k": top_k})
    rows = res.fetchall()
    # map rows to simple dicts for convenience
    out = []
    for r in rows:
        out.append({"id": r.id, "text": r.text, "kind": r.kind})
    return out

def join_context(short_ctx: str, long_ctx: list[dict]) -> str:
    long_text = "\n".join([f"- ({m['kind']}) {m['text']}" for m in long_ctx]) if long_ctx else "(no long-term memory)"
    return f"SHORT-TERM:\n{short_ctx}\n\nLONG-TERM MEMORY:\n{long_text}"
