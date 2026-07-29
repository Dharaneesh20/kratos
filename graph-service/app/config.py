from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "graph-service"
    SERVICE_PORT: int = 8002
    SNAP_TOLERANCE_M: float = 5.0
    WEIGHT_BETWEENNESS: float = 0.6
    WEIGHT_CLOSENESS: float = 0.25
    WEIGHT_DEGREE: float = 0.15
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    DEFAULT_ASSUMED_SPEED_KMH: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
