"""
Session management service for conversation state and persistence.
Handles conversation sessions, message storage, and session lifecycle.
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from .base import BaseService, SessionManagerInterface
from ..core.exceptions import SessionError
from ..core.config import settings
from ..models.database import db_manager, Conversation, Message
from ..models.schemas import MessageType, ConversationStatus, MessageResponse


class SessionManagerService(BaseService, SessionManagerInterface):
    """Service for managing conversation sessions and message history."""
    
    def __init__(self):
        super().__init__()
        self.session_settings = settings.session_settings
    
    async def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            Session ID
            
        Raises:
            SessionError: If session creation fails
        """
        try:
            session_id = str(uuid.uuid4())
            
            async with db_manager.async_session() as db_session:
                conversation = Conversation(
                    id=session_id,
                    status=ConversationStatus.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                db_session.add(conversation)
                await db_session.commit()
            
            self.logger.info("Session created", session_id=session_id)
            return session_id
            
        except Exception as e:
            self.logger.error("Failed to create session", error=str(e))
            raise SessionError(
                f"Failed to create session: {str(e)}",
                error_code="SESSION_CREATION_ERROR"
            )
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data or None if not found
            
        Raises:
            SessionError: If session retrieval fails
        """
        try:
            async with db_manager.async_session() as db_session:
                result = await db_session.execute(
                    select(Conversation).where(Conversation.id == session_id)
                )
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    return None
                
                return {
                    "id": conversation.id,
                    "status": conversation.status,
                    "created_at": conversation.created_at,
                    "updated_at": conversation.updated_at
                }
                
        except Exception as e:
            self.logger.error("Failed to get session", session_id=session_id, error=str(e))
            raise SessionError(
                f"Failed to get session: {str(e)}",
                error_code="SESSION_RETRIEVAL_ERROR"
            )
    
    async def update_session(
        self, 
        session_id: str, 
        data: Dict[str, Any]
    ) -> None:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            data: Data to update
            
        Raises:
            SessionError: If session update fails
        """
        try:
            async with db_manager.async_session() as db_session:
                # Check if session exists
                result = await db_session.execute(
                    select(Conversation).where(Conversation.id == session_id)
                )
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    raise SessionError(
                        f"Session {session_id} not found",
                        error_code="SESSION_NOT_FOUND"
                    )
                
                # Update allowed fields
                update_data = {"updated_at": datetime.utcnow()}
                
                if "status" in data:
                    update_data["status"] = data["status"]
                
                await db_session.execute(
                    update(Conversation)
                    .where(Conversation.id == session_id)
                    .values(**update_data)
                )
                
                await db_session.commit()
            
            self.logger.info("Session updated", session_id=session_id, data=data)
            
        except SessionError:
            raise
        except Exception as e:
            self.logger.error("Failed to update session", session_id=session_id, error=str(e))
            raise SessionError(
                f"Failed to update session: {str(e)}",
                error_code="SESSION_UPDATE_ERROR"
            )
    
    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session identifier
            
        Raises:
            SessionError: If session deletion fails
        """
        try:
            async with db_manager.async_session() as db_session:
                # Delete conversation (messages will be deleted by cascade)
                await db_session.execute(
                    delete(Conversation).where(Conversation.id == session_id)
                )
                
                await db_session.commit()
            
            self.logger.info("Session deleted", session_id=session_id)
            
        except Exception as e:
            self.logger.error("Failed to delete session", session_id=session_id, error=str(e))
            raise SessionError(
                f"Failed to delete session: {str(e)}",
                error_code="SESSION_DELETION_ERROR"
            )
    
    async def add_message(
        self,
        session_id: str,
        message_type: MessageType,
        content: str,
        extra_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a message to a session.
        
        Args:
            session_id: Session identifier
            message_type: Type of message (user/assistant/system)
            content: Message content
            extra_data: Optional extra data
            
        Returns:
            Message ID
            
        Raises:
            SessionError: If message addition fails
        """
        try:
            message_id = str(uuid.uuid4())
            
            async with db_manager.async_session() as db_session:
                # Verify session exists
                result = await db_session.execute(
                    select(Conversation).where(Conversation.id == session_id)
                )
                conversation = result.scalar_one_or_none()
                
                if not conversation:
                    raise SessionError(
                        f"Session {session_id} not found",
                        error_code="SESSION_NOT_FOUND"
                    )
                
                # Create message
                message = Message(
                    id=message_id,
                    session_id=session_id,
                    type=message_type,
                    content=content,
                    timestamp=datetime.utcnow(),
                    extra_data=extra_data
                )
                
                db_session.add(message)
                
                # Update session timestamp
                await db_session.execute(
                    update(Conversation)
                    .where(Conversation.id == session_id)
                    .values(updated_at=datetime.utcnow())
                )
                
                await db_session.commit()
            
            self.logger.info(
                "Message added to session",
                session_id=session_id,
                message_id=message_id,
                message_type=message_type
            )
            
            return message_id
            
        except SessionError:
            raise
        except Exception as e:
            self.logger.error("Failed to add message", session_id=session_id, error=str(e))
            raise SessionError(
                f"Failed to add message: {str(e)}",
                error_code="MESSAGE_ADDITION_ERROR"
            )
    
    async def get_conversation_history(
        self, 
        session_id: str, 
        limit: Optional[int] = None
    ) -> List[MessageResponse]:
        """
        Get conversation history for a session.
        
        Args:
            session_id: Session identifier
            limit: Optional limit on number of messages
            
        Returns:
            List of MessageResponse Pydantic models
            
        Raises:
            SessionError: If history retrieval fails
        """
        try:
            limit = limit or self.session_settings.max_conversation_history
            
            async with db_manager.async_session() as db_session:
                result = await db_session.execute(
                    select(Message)
                    .where(Message.session_id == session_id)
                    .order_by(Message.timestamp.desc())
                    .limit(limit)
                )
                messages_db = result.scalars().all()
                
                return [MessageResponse.model_validate(message) for message in reversed(messages_db)]
                
        except Exception as e:
            self.logger.error("Failed to get conversation history", session_id=session_id, error=str(e))
            raise SessionError(
                f"Failed to get conversation history: {str(e)}",
                error_code="HISTORY_RETRIEVAL_ERROR"
            )
    
    async def cleanup_expired_sessions(self) -> int:
        """
        Clean up expired sessions.
        
        Returns:
            Number of sessions cleaned up
            
        Raises:
            SessionError: If cleanup fails
        """
        try:
            expiry_time = datetime.utcnow() - timedelta(
                minutes=self.session_settings.timeout_minutes
            )
            
            async with db_manager.async_session() as db_session:
                # Find expired sessions
                result = await db_session.execute(
                    select(Conversation)
                    .where(
                        Conversation.updated_at < expiry_time,
                        Conversation.status == ConversationStatus.ACTIVE
                    )
                )
                expired_sessions = result.scalars().all()
                
                # Mark as expired
                expired_count = 0
                for session in expired_sessions:
                    await db_session.execute(
                        update(Conversation)
                        .where(Conversation.id == session.id)
                        .values(status=ConversationStatus.EXPIRED)
                    )
                    expired_count += 1
                
                await db_session.commit()
            
            if expired_count > 0:
                self.logger.info("Expired sessions cleaned up", count=expired_count)
            
            return expired_count
            
        except Exception as e:
            self.logger.error("Failed to cleanup expired sessions", error=str(e))
            raise SessionError(
                f"Failed to cleanup sessions: {str(e)}",
                error_code="CLEANUP_ERROR"
            )
    
    async def get_session_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about sessions.
        
        Returns:
            Dictionary with session statistics
        """
        try:
            async with db_manager.async_session() as db_session:
                # Count sessions by status
                result = await db_session.execute(
                    select(Conversation.status, db_session.query(Conversation).count())
                    .group_by(Conversation.status)
                )
                
                stats = {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "completed_sessions": 0,
                    "expired_sessions": 0,
                    "total_messages": 0
                }
                
                # Count sessions
                for status, count in result:
                    stats["total_sessions"] += count
                    if status == ConversationStatus.ACTIVE:
                        stats["active_sessions"] = count
                    elif status == ConversationStatus.COMPLETED:
                        stats["completed_sessions"] = count
                    elif status == ConversationStatus.EXPIRED:
                        stats["expired_sessions"] = count
                
                # Count total messages
                message_result = await db_session.execute(
                    select(Message).count()
                )
                stats["total_messages"] = message_result.scalar()
                
                return stats
                
        except Exception as e:
            self.logger.error("Failed to get session statistics", error=str(e))
            return {"error": f"Failed to get statistics: {str(e)}"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the session manager."""
        base_health = await super().health_check()
        
        try:
            stats = await self.get_session_statistics()
            base_health.update({
                "session_statistics": stats,
                "status": "healthy"
            })
            
        except Exception as e:
            base_health.update({
                "status": "unhealthy",
                "error": str(e)
            })
        
        return base_health
