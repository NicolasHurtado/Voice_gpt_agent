"""
Chat service for intelligent conversation using OpenAI GPT.
Manages conversation context and generates contextual responses.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import AsyncOpenAI

from .base import BaseService, ChatServiceInterface
from .session_manager import SessionManagerService
from ..core.exceptions import GPTServiceError, RateLimitError
from ..core.config import settings
from ..models.schemas import MessageType


class ChatService(BaseService, ChatServiceInterface):
    """Service for managing GPT-powered conversations."""
    
    def __init__(self, session_manager: SessionManagerService):
        super().__init__(session_manager=session_manager)
        self.client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.session_manager = session_manager
        self.openai_settings = settings.openai_settings
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the voice agent."""
        return """You are a helpful and friendly AI voice assistant. You excel at natural conversation and providing useful information.

Key characteristics:
- Speak naturally and conversationally, as if talking to a friend
- Keep responses concise but informative (aim for 1-3 sentences for voice)
- Be helpful, empathetic, and engaging
- When appropriate, ask follow-up questions to continue the conversation
- If you need clarification, ask for it clearly
- Avoid overly technical jargon unless specifically requested
- Remember the conversation context to provide relevant responses

You are communicating through voice, so:
- Avoid using markdown, special formatting, or symbols
- Spell out numbers and abbreviations when they would be unclear spoken
- Use natural speech patterns and contractions
- Structure your responses for easy listening

Current conversation context will be provided with each message."""
    
    async def generate_response(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> tuple[str, str]:
        """
        Generate a response to a user message with conversation context.
        
        Args:
            message: User's message
            session_id: Session identifier for conversation context
            context: Additional context information
            
        Returns:
            Tuple of (generated response text, assistant message ID)
            
        Raises:
            GPTServiceError: If response generation fails
        """
        try:
            # Get conversation history
            conversation_history = await self.session_manager.get_conversation_history(
                session_id
            )
            
            # Build messages for GPT
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            for msg in conversation_history[-settings.session_settings.max_conversation_history:]:
                role = "user" if msg.type == MessageType.USER else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Add context information if provided
            if context:
                context_info = self._format_context(context)
                if context_info:
                    messages.append({
                        "role": "system",
                        "content": f"Additional context: {context_info}"
                    })
            
            # Generate response using GPT
            response = await self.client.chat.completions.create(
                model=self.openai_settings.model,
                messages=messages,
                max_tokens=500,  # Limit for voice responses
                temperature=0.7,  # Balanced creativity
                presence_penalty=0.1,  # Slight penalty for repetition
                frequency_penalty=0.1  # Slight penalty for frequency
            )
            
            assistant_response = response.choices[0].message.content
            
            # Save messages to session
            user_message_id = await self.session_manager.add_message(
                session_id, 
                MessageType.USER, 
                message,
                extra_data={"context": context}
            )
            
            assistant_message_id = await self.session_manager.add_message(
                session_id, 
                MessageType.ASSISTANT, 
                assistant_response,
                extra_data={
                    "model": self.openai_settings.model,
                    "tokens_used": response.usage.total_tokens if response.usage else None
                }
            )
            
            self.logger.info(
                "Response generated successfully",
                session_id=session_id,
                message_length=len(message),
                response_length=len(assistant_response),
                tokens_used=response.usage.total_tokens if response.usage else None,
                assistant_message_id=assistant_message_id
            )
            
            return assistant_response, assistant_message_id
            
        except Exception as e:
            if "rate_limit" in str(e).lower():
                raise RateLimitError(
                    "OpenAI API rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            
            self.logger.error("Failed to generate response", error=str(e))
            raise GPTServiceError(
                f"Failed to generate response: {str(e)}",
                error_code="RESPONSE_GENERATION_ERROR"
            )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format additional context information for the GPT prompt.
        
        Args:
            context: Context dictionary
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        if "user_location" in context:
            context_parts.append(f"User location: {context['user_location']}")
        
        if "time_of_day" in context:
            context_parts.append(f"Time: {context['time_of_day']}")
        
        if "user_preference" in context:
            context_parts.append(f"User preferences: {context['user_preference']}")
        
        if "conversation_topic" in context:
            context_parts.append(f"Topic: {context['conversation_topic']}")
        
        return "; ".join(context_parts)
    
    async def generate_streaming_response(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """
        Generate a streaming response for real-time conversation.
        
        Args:
            message: User's message
            session_id: Session identifier
            context: Additional context
            
        Yields:
            Response chunks as they're generated
        """
        try:
            # Get conversation history
            conversation_history = await self.session_manager.get_conversation_history(
                session_id
            )
            
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            for msg in conversation_history[-settings.session_settings.max_conversation_history:]:
                role = "user" if msg.type == MessageType.USER else "assistant"
                messages.append({
                    "role": role,
                    "content": msg.content
                })
            
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Generate streaming response
            stream = await self.client.chat.completions.create(
                model=self.openai_settings.model,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                stream=True
            )
            
            full_response = ""
            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Save messages after streaming is complete
            await self.session_manager.add_message(
                session_id, 
                MessageType.USER, 
                message,
                extra_data={"context": context}
            )
            
            await self.session_manager.add_message(
                session_id, 
                MessageType.ASSISTANT, 
                full_response,
                extra_data={
                    "model": self.openai_settings.model,
                    "streaming": True
                }
            )
            
        except Exception as e:
            self.logger.error("Streaming response failed", error=str(e))
            raise GPTServiceError(
                f"Streaming response failed: {str(e)}",
                error_code="STREAMING_ERROR"
            )
    
    async def summarize_conversation(self, session_id: str) -> str:
        """
        Generate a summary of the conversation.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Conversation summary
        """
        try:
            conversation_history = await self.session_manager.get_conversation_history(
                session_id
            )
            
            if not conversation_history:
                return "No conversation to summarize."
            
            # Create conversation text
            conversation_text = "\n".join([
                f"{msg.type.value}: {msg.content}"
                for msg in conversation_history
            ])
            
            # Generate summary
            messages = [
                {
                    "role": "system",
                    "content": "Summarize the following conversation concisely, highlighting key topics and outcomes:"
                },
                {
                    "role": "user",
                    "content": conversation_text
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=self.openai_settings.model,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            
            summary = response.choices[0].message.content
            
            self.logger.info(
                "Conversation summary generated",
                session_id=session_id,
                summary_length=len(summary)
            )
            
            return summary
            
        except Exception as e:
            self.logger.error("Failed to summarize conversation", error=str(e))
            raise GPTServiceError(
                f"Failed to summarize conversation: {str(e)}",
                error_code="SUMMARIZATION_ERROR"
            )
    
    async def get_conversation_insights(self, session_id: str) -> Dict[str, Any]:
        """
        Analyze conversation for insights and patterns.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary with conversation insights
        """
        try:
            conversation_history = await self.session_manager.get_conversation_history(
                session_id
            )
            
            if not conversation_history:
                return {"message": "No conversation data available"}
            
            # Basic analytics
            user_messages = [msg for msg in conversation_history if msg.type == MessageType.USER]
            assistant_messages = [msg for msg in conversation_history if msg.type == MessageType.ASSISTANT]
            
            insights = {
                "total_messages": len(conversation_history),
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "average_user_message_length": sum(len(msg.content) for msg in user_messages) / len(user_messages) if user_messages else 0,
                "average_assistant_message_length": sum(len(msg.content) for msg in assistant_messages) / len(assistant_messages) if assistant_messages else 0,
                "conversation_duration": None,
                "topics": []
            }
            
            # Calculate conversation duration
            if conversation_history:
                start_time = conversation_history[0].timestamp
                end_time = conversation_history[-1].timestamp
                if isinstance(start_time, str):
                    start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                if isinstance(end_time, str):
                    end_time = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                
                duration = (end_time - start_time).total_seconds()
                insights["conversation_duration"] = duration
            
            return insights
            
        except Exception as e:
            self.logger.error("Failed to generate insights", error=str(e))
            return {"error": f"Failed to generate insights: {str(e)}"}
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the chat service."""
        base_health = await super().health_check()
        
        try:
            # Test with a simple message
            test_response = await self.client.chat.completions.create(
                model=self.openai_settings.model,
                messages=[
                    {"role": "system", "content": "You are a test assistant."},
                    {"role": "user", "content": "Say 'test successful'"}
                ],
                max_tokens=10
            )
            
            base_health.update({
                "gpt_model": self.openai_settings.model,
                "test_response": test_response.choices[0].message.content,
                "status": "healthy"
            })
            
        except Exception as e:
            base_health.update({
                "status": "unhealthy",
                "error": str(e)
            })
        
        return base_health
