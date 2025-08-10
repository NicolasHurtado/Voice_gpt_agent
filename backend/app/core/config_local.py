"""
Configuration for local model deployment.
Extended configuration for running with gpt-oss via Ollama.
"""

from typing import List, Optional
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class OllamaSettings(BaseModel):
    """Ollama-specific configuration settings."""
    base_url: str = "http://localhost:11434/v1"
    model_name: str = "gpt-oss:20b"
    api_key: str = "ollama"  # Dummy key for Ollama
    max_tokens: int = 300
    temperature: float = 0.7
    timeout: int = 120  # seconds


class LocalModelSettings(BaseModel):
    """Local model configuration settings."""
    use_local_model: bool = False
    ollama_settings: OllamaSettings = OllamaSettings()
    fallback_to_openai: bool = True


class LocalSettings(BaseSettings):
    """Extended settings for local deployment."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Local model configuration
    use_local_model: bool = False
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model_name: str = "gpt-oss:20b"
    ollama_timeout: int = 120
    fallback_to_openai: bool = True
    
    # OpenAI configuration (for fallback)
    openai_api_key: Optional[str] = None
    
    @property
    def local_model_settings(self) -> LocalModelSettings:
        """Get local model configuration as a structured object."""
        return LocalModelSettings(
            use_local_model=self.use_local_model,
            ollama_settings=OllamaSettings(
                base_url=self.ollama_base_url,
                model_name=self.ollama_model_name,
                timeout=self.ollama_timeout
            ),
            fallback_to_openai=self.fallback_to_openai
        )


# Global local settings instance
local_settings = LocalSettings()
