from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json
import os

class Settings(BaseSettings):
    WAY_API_URL: str = "http://localhost:8000"
    WAY_TIMEOUT: int = 10
    USE_MOCK: bool = True
    PORT: int = 8001
    LOG_DIR: str = "logs"
    CORS_ORIGINS_JSON: str = '["http://localhost:5173", "http://localhost:3000"]'

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def CORS_ORIGINS(self) -> List[str]:
        try:
            return json.loads(self.CORS_ORIGINS_JSON)
        except:
            return ["http://localhost:5173"]

config = Settings()

def validate_config():
    # สร้างโฟลเดอร์ logs ถ้ายังไม่มี
    if not os.path.exists(config.LOG_DIR):
        os.makedirs(config.LOG_DIR)
    print(f"✅ Log directory ready at: {config.LOG_DIR}")
