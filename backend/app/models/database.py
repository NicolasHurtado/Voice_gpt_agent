"""
SQLAlchemy database models for persistent storage.
Uses async SQLAlchemy for non-blocking database operations.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID

from .schemas import MessageType, ConversationStatus
from ..core.config import settings

# Create base class for all models
Base = declarative_base()


class Conversation(Base):
    """Model for conversation sessions."""
    
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, status={self.status})>"


class Message(Base):
    """Model for individual messages in conversations."""
    
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)
    
    # Relationship with conversation
    conversation = relationship("Conversation", back_populates="messages")
    
    def __repr__(self) -> str:
        return f"<Message(id={self.id}, type={self.type}, session_id={self.session_id})>"


# Database session management
class DatabaseManager:
    """Manages database connections and sessions."""
    
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            echo=settings.debug,
            future=True
        )
        self.async_session = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    async def create_tables(self) -> None:
        """Create all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    
    async def drop_tables(self) -> None:
        """Drop all database tables."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def get_session(self) -> AsyncSession:
        """Get an async database session."""
        async with self.async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self) -> None:
        """Close the database engine."""
        await self.engine.dispose()


# Global database manager instance
db_manager = DatabaseManager(settings.database_url)
