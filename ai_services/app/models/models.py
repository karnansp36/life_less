# models.py
from sqlalchemy import String, Integer, Text, ForeignKey, Boolean, DateTime, Float, JSON, Time, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TIMESTAMP, ARRAY
from pgvector.sqlalchemy import Vector
from datetime import datetime, time
from app.database import Base
from typing import Dict, Any, List
import enum

# Add this if you don't have a settings module, or replace with your actual value
EMBEDDING_DIMENSIONS = 768  # Typical dimension for OpenAI embeddings

class UserRole(str, enum.Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(50), default="UTC")
    wake_time: Mapped[time] = mapped_column(Time, default=time(7, 0))
    sleep_time: Mapped[time] = mapped_column(Time, default=time(23, 0))
    work_hours_start: Mapped[time] = mapped_column(Time, default=time(9, 0))
    work_hours_end: Mapped[time] = mapped_column(Time, default=time(17, 0))
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    # Relationships (NO main_app_user_id field here!)
    habits: Mapped[List["Habit"]] = relationship(back_populates="user")
    expenses: Mapped[List["Expense"]] = relationship(back_populates="user")
    conversations: Mapped[List["Conversation"]] = relationship(back_populates="user")
    memories: Mapped[List["Memory"]] = relationship(back_populates="user")
    goals: Mapped[List["Goal"]] = relationship(back_populates="user")
    emails: Mapped[List["EmailAccount"]] = relationship(back_populates="user")

class Conversation(Base):
    __tablename__ = "conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    context: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="conversations")
    messages: Mapped[List["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)  # ← This should NOT be nullable
    role: Mapped[str] = mapped_column(String(20))  # user, assistant, system
    content: Mapped[str] = mapped_column(Text)
    # Changed from 'metadata' to 'message_metadata' to avoid SQLAlchemy conflict
    message_metadata: Mapped[Dict[str, Any]] = mapped_column(JSON, default={})  # Store agent info, emotions, etc.
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
    user: Mapped["User"] = relationship()

class MemoryType(str, enum.Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    PERSONAL = "personal"
    WORK = "work"
    HEALTH = "health"
    FINANCE = "finance"

class Memory(Base):
    __tablename__ = "memories"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    memory_type: Mapped[MemoryType] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    importance: Mapped[float] = mapped_column(Float, default=1.0)  # 0.0-1.0 scale
    embedding: Mapped[List[float]] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(50)), default=[])
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_accessed: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="memories")

class Habit(Base):
    __tablename__ = "habits"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    frequency: Mapped[str] = mapped_column(String(50))  # daily, weekly, monthly
    target_count: Mapped[int] = mapped_column(Integer, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    longest_streak: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    
    user: Mapped["User"] = relationship(back_populates="habits")
    completions: Mapped[List["HabitCompletion"]] = relationship(back_populates="habit", cascade="all, delete-orphan")

class HabitCompletion(Base):
    __tablename__ = "habit_completions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    habit_id: Mapped[int] = mapped_column(ForeignKey("habits.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    
    habit: Mapped["Habit"] = relationship(back_populates="completions")

class ExpenseCategory(str, enum.Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    HEALTH = "health"
    EDUCATION = "education"
    BILLS = "bills"
    OTHER = "other"

class Expense(Base):
    __tablename__ = "expenses"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD")
    category: Mapped[ExpenseCategory] = mapped_column(String(20))
    description: Mapped[str] = mapped_column(String(200))
    date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    receipt_url: Mapped[str] = mapped_column(String(500), nullable=True)
    tags: Mapped[List[str]] = mapped_column(ARRAY(String(50)), default=[])
    
    user: Mapped["User"] = relationship(back_populates="expenses")

class GoalStatus(str, enum.Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class Goal(Base):
    __tablename__ = "goals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(String(20), default=GoalStatus.PLANNING)
    progress: Mapped[float] = mapped_column(Float, default=0.0)  # 0.0-1.0
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    
    user: Mapped["User"] = relationship(back_populates="goals")
    milestones: Mapped[List["Milestone"]] = relationship(back_populates="goal", cascade="all, delete-orphan")

class Milestone(Base):
    __tablename__ = "milestones"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)
    target_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    goal: Mapped["Goal"] = relationship(back_populates="milestones")

class EmailAccount(Base):
    __tablename__ = "email_accounts"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    email: Mapped[str] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(50))  # gmail, outlook, etc.
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_synced: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    user: Mapped["User"] = relationship(back_populates="emails")

class EmailMessage(Base):
    __tablename__ = "email_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("email_accounts.id"), index=True)
    message_id: Mapped[str] = mapped_column(String(500))
    subject: Mapped[str] = mapped_column(String(500))
    sender: Mapped[str] = mapped_column(String(255))
    recipients: Mapped[List[str]] = mapped_column(ARRAY(String(255)))
    body: Mapped[str] = mapped_column(Text)
    importance: Mapped[str] = mapped_column(String(10), default="normal")  # low, normal, high
    category: Mapped[str] = mapped_column(String(50), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    received_at: Mapped[datetime] = mapped_column(DateTime)
    
    account: Mapped["EmailAccount"] = relationship()