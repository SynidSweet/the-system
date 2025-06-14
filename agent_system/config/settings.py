import os
from typing import Optional
try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    google_api_key: Optional[str] = None
    
    # Google OAuth
    google_client_id: Optional[str] = None
    google_client_secret: Optional[str] = None
    
    # System Configuration
    system_secret_key: str = "default-secret-key-change-me"
    database_url: str = "sqlite:///data/agent_system.db"
    max_concurrent_agents: int = 3
    default_timeout_seconds: int = 300
    environment: str = "development"
    debug_mode: bool = True
    supervisor_check_interval: int = 60
    
    # Model Configuration
    default_model_provider: str = "google"
    default_model_name: str = "gemini-2.0-flash-exp"
    default_temperature: float = 0.1
    default_max_tokens: int = 4000
    
    # Safety Limits
    max_recursion_depth: int = 10
    max_tool_calls_per_task: int = 50
    memory_limit_mb: int = 1024
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()