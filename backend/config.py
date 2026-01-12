"""
Configuration and environment settings for WUT Backend
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
import json
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # ==================== API Configuration ====================
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # ==================== WAY API Configuration ====================
    WAY_API_URL: str = "http://localhost:8000"
    WAY_TIMEOUT: int = 10
    USE_MOCK: bool = False
    
    # ==================== CORS Configuration ====================
    # Use str instead of List to avoid pydantic-settings issues
    CORS_ORIGINS: str = "*"
    
    # ==================== Logging Configuration ====================
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # ==================== Decision Engine Thresholds ====================
    CONFIDENCE_THRESHOLD: float = 0.70
    ESCALATION_CONFIDENCE_THRESHOLD: float = 0.50
    HIGH_CONFIDENCE_THRESHOLD: float = 0.85
    
    # ==================== Ticket Configuration ====================
    TICKET_PREFIX: str = "TK"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    def get_cors_origins(self) -> List[str]:
        """Parse CORS_ORIGINS into a list"""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        # Try to parse as JSON array
        try:
            origins = json.loads(self.CORS_ORIGINS)
            if isinstance(origins, list):
                return origins
        except json.JSONDecodeError:
            pass
        # Split by comma
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


# =============================================================================
# ⚠️ CRITICAL: Create global settings instance
# This is what other modules import: `from config import settings`
# =============================================================================
settings = Settings()


# =============================================================================
# Helper Functions
# =============================================================================
def validate_config() -> None:
    """Validate and print configuration on startup"""
    print("\n" + "=" * 50)
    print("📋 WUT Backend Configuration")
    print("=" * 50)
    print(f"🌐 Host: {settings.HOST}:{settings.PORT}")
    print(f"🔗 WAY API: {settings.WAY_API_URL}")
    print(f"⏱️  WAY Timeout: {settings.WAY_TIMEOUT}s")
    print(f"🎭 Mock Mode: {'ON' if settings.USE_MOCK else 'OFF'}")
    print(f"📊 Log Level: {settings.LOG_LEVEL}")
    print(f"🎯 Confidence Threshold: {settings.CONFIDENCE_THRESHOLD}")
    print("=" * 50 + "\n")
    
    if settings.USE_MOCK:
        print("⚠️  WARNING: Running in MOCK mode")
        print("   WAY API will not be called, using mock responses\n")


def get_settings() -> Settings:
    """Get the global settings instance (for dependency injection)"""
    return settings
