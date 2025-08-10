"""
Local chat service using gpt-oss via Ollama.
Alternative to OpenAI GPT for local inference.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import OpenAI

from .base import BaseService, ChatServiceInterface
from .session_manager import SessionManagerService
from ..core.exceptions import GPTServiceError
from ..core.config import settings
from ..models.schemas import MessageType


class LocalChatService(BaseService, ChatServiceInterface):
    """Service for managing conversations using local gpt-oss model via Ollama."""
    
    def __init__(self, session_manager: SessionManagerService):
        super().__init__(session_manager=session_manager)
        # Configure OpenAI client to use local Ollama
        self.client = OpenAI(
            base_url="http://localhost:11434/v1",  # Local Ollama API
            api_key="ollama"  # Dummy key for Ollama
        )
        self.session_manager = session_manager
        self.model_name = "gpt-oss:20b"  # Use 20B model for 16GB RAM
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the local voice agent."""
        return """You are a helpful and friendly AI voice assistant running locally. You excel at natural conversation and providing useful information.

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

You are running locally on the user's machine, which means:
- You respect user privacy completely
- You work offline without internet connection
- You provide fast, local responses

Current conversation context will be provided with each message."""
    
    async def generate_response(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a response using local gpt-oss model.
        
        Args:
            message: User's message
            session_id: Session identifier for conversation context
            context: Additional context information
            
        Returns:
            Generated response text
            
        Raises:
            GPTServiceError: If response generation fails
        """
        try:
            # Get conversation history
            conversation_history = await self.session_manager.get_conversation_history(
                session_id
            )
            
            # Build messages for local GPT
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history (limit to last 10 messages for memory efficiency)
            for msg in conversation_history[-10:]:
                role = "user" if msg["type"] == MessageType.USER else "assistant"
                messages.append({
                    "role": role,
                    "content": msg["content"]
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
            
            # Generate response using local model
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=300,  # Shorter for local model efficiency
                temperature=0.7,
                # Note: local models might not support all OpenAI parameters
            )
            
            assistant_response = response.choices[0].message.content
            
            # Save messages to session
            await self.session_manager.add_message(
                session_id, 
                MessageType.USER, 
                message,
                extra_data={"context": context, "model": "local"}
            )
            
            await self.session_manager.add_message(
                session_id, 
                MessageType.ASSISTANT, 
                assistant_response,
                extra_data={
                    "model": self.model_name,
                    "local_inference": True
                }
            )
            
            self.logger.info(
                "Local response generated successfully",
                session_id=session_id,
                message_length=len(message),
                response_length=len(assistant_response),
                model=self.model_name
            )
            
            return assistant_response
            
        except Exception as e:
            self.logger.error("Failed to generate local response", error=str(e))
            raise GPTServiceError(
                f"Failed to generate response using local model: {str(e)}",
                error_code="LOCAL_RESPONSE_GENERATION_ERROR"
            )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format additional context information for the prompt."""
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
    
    async def check_ollama_connection(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": "Hello, are you working?"}
                ],
                max_tokens=10
            )
            return True
        except Exception as e:
            self.logger.error("Ollama connection check failed", error=str(e))
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the local chat service."""
        base_health = await super().health_check()
        
        try:
            ollama_available = await self.check_ollama_connection()
            
            base_health.update({
                "model": self.model_name,
                "ollama_available": ollama_available,
                "inference_type": "local",
                "status": "healthy" if ollama_available else "unhealthy"
            })
            
            if not ollama_available:
                base_health["error"] = "Ollama not available or model not loaded"
            
        except Exception as e:
            base_health.update({
                "status": "unhealthy",
                "error": str(e)
            })
        
        return base_health
