from collections import defaultdict, deque
from typing import Deque, Tuple, List, Dict, Any
from sqlalchemy import select, text as sql_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.settings import settings
from app.models.conversation import Conversation, Message, UserMemory
from app.services.embeddings import embed_text

# ------- Short-term in-memory (fast) -------
# user_id -> deque[(role, content)]
_SHORT_MEMORY: dict[str, Deque[Tuple[str, str]]] = defaultdict(
    lambda: deque(maxlen=settings.SHORT_MEMORY_MAXLEN)
)


def short_append(user_id: str, role: str, content: str) -> None:
    """Append to short-term memory (RAM only)."""
    _SHORT_MEMORY[user_id].append((role, content))


def short_context(user_id: str, limit: int = 10) -> str:
    """Return last N messages for the user from short-term memory."""
    msgs = list(_SHORT_MEMORY[user_id])[-limit:]
    lines: List[str] = []
    for role, content in msgs:
        prefix = "User" if role == "user" else "Assistant"
        lines.append(f"{prefix}: {content}")
    return "\n".join(lines) if lines else "(no prior messages)"


# ------- DB persistence -------
async def ensure_conversation(session: AsyncSession, user_id: str) -> Conversation:
    """Ensure a conversation exists for the user, else create it."""
    q = select(Conversation).where(Conversation.user_id == user_id).order_by(
        Conversation.created_at.desc()  # Get most recent conversation
    )
    res = await session.execute(q)
    conv = res.scalars().first()
    
    if conv:
        return conv
        
    # Create new conversation if none exists
    conv = Conversation(user_id=user_id)
    session.add(conv)
    await session.flush()
    return conv


async def persist_message(
    session: AsyncSession, 
    conversation_id: int, 
    user_id: str, 
    role: str, 
    content: str
) -> None:
    """Persist a chat message to DB."""
    msg = Message(
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
    )
    session.add(msg)
    await session.flush()


# ------- Long-term memory (RAG over personal data) -------
async def add_user_memory(
    session: AsyncSession, 
    user_id: str, 
    text: str, 
    kind: str = "fact"
) -> None:
    """Store text with its embedding in long-term memory."""
    vec = embed_text(text)  # Get embedding vector
    
    # Convert vector to PostgreSQL vector format string
    vec_str = "[" + ",".join(map(str, vec)) + "]"
    
    stmt = sql_text("""
        INSERT INTO user_memory (user_id, text, kind, embedding)
        VALUES (:user_id, :text, :kind, (:embedding)::vector)
    """)
    
    await session.execute(
        stmt,
        {
            "user_id": user_id,
            "text": text,
            "kind": kind,
            "embedding": vec_str
        }
    )
    await session.commit()


async def semantic_retrieve_user_memory(
    session: AsyncSession, 
    user_id: str, 
    query: str, 
    top_k: int | None = None
) -> list[dict]:
    top_k = top_k or settings.RAG_TOP_K
    qvec = embed_text(query)  # Get embedding as list[float]
    
    # Convert to PostgreSQL vector literal format
    vec_str = "[" + ",".join(map(str, qvec)) + "]"
    
    sql = sql_text("""
        SELECT id, user_id, kind, text, created_at
        FROM user_memory
        WHERE user_id = :uid
        ORDER BY embedding <#> (:vec_str)::vector
        LIMIT :k
    """)
    
    result = await session.execute(sql, {
        "uid": user_id,
        "vec_str": vec_str,  # Pass as string
        "k": top_k
    })
    
    return [dict(row) for row in result.mappings()]

def join_context(short_ctx: str, long_ctx: List[Dict[str, Any]]) -> str:
    """Merge short-term and long-term memory into one context string."""
    if not long_ctx:
        return f"Recent conversation:\n{short_ctx}\n\n(No relevant long-term memory)"
    
    long_term_str = "\n".join(
        f"- [{mem['kind']}] {mem['text']}" 
        for mem in long_ctx
    )
    
    return (
        f"Recent conversation:\n{short_ctx}\n\n"
        f"Relevant long-term memories:\n{long_term_str}"
    )