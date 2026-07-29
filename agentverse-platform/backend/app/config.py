import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "kratos-backend"
    VISION_SERVICE_URL: str = os.getenv("VISION_SERVICE_URL", "http://localhost:8001")
    GRAPH_SERVICE_URL: str = os.getenv("GRAPH_SERVICE_URL", "http://localhost:8002")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./kratos.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-kratos-2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    NIM_ENDPOINT: str = os.getenv("NIM_ENDPOINT", "https://integrate.api.nvidia.com/v1")
    NIM_MODEL: str = os.getenv("NIM_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1")
    NIM_API_KEY: str = os.getenv("NIM_API_KEY", "")
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    CUOPT_API_KEY: str = os.getenv("CUOPT_API_KEY", "")
    CUOPT_ENDPOINT: str = os.getenv("CUOPT_ENDPOINT", "https://integrate.api.nvidia.com/v1/cuopt")

    @property
    def active_nvidia_key(self) -> str:
        return self.NVIDIA_API_KEY or self.CUOPT_API_KEY or self.NIM_API_KEY

    REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./reports")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
