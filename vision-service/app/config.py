from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "vision-service"
    SERVICE_VERSION: str = "0.1.0"
    SERVICE_PORT: int = 8001

    REDIS_URL: str = "redis://localhost:6379/0"
    CACHE_DIR: str = "cache"
    JOB_TTL_SECONDS: int = 86400
    WS_POLL_INTERVAL_SECONDS: float = 1.0

    CRS_DEFAULT: str = "EPSG:4326"

    DATASET_CACHE_TTL_SECONDS: int = 86400
    PROVIDER_MAX_RETRIES: int = 3
    PROVIDER_BACKOFF_BASE_SECONDS: int = 1

    DATA_DIR: str = "data"
    TRAIN_SAT_SUFFIX: str = "_sat.jpg"
    TRAIN_MASK_SUFFIX: str = "_mask.png"

    IMG_SIZE: int = 512
    TILE_SIZE: int = 512
    TILE_OVERLAP: int = 64
    MASK_THRESHOLD: float = 0.5
    MIN_BRANCH_LEN_PX: int = 15
    SIMPLIFY_TOLERANCE_PX: float = 1.5

    WEIGHTS_DIR: str = "weights"
    MODEL_CHECKPOINT: str = "weights/roadnet.pt"
    ENCODER_NAME: str = "resnet34"
    DEFAULT_MODEL: str = "segformer"

    SEGFORMER_CHECKPOINT: str = "weights/segformer"
    DEEPLABV3PLUS_CHECKPOINT: str = "weights/deeplabv3plus.pt"

    SENTINEL_HUB_CLIENT_ID: str = ""
    SENTINEL_HUB_CLIENT_SECRET: str = ""
    SENTINEL_TOKEN_URL: str = "https://services.sentinel-hub.com/oauth/token"
    SENTINEL_PROCESS_URL: str = "https://services.sentinel-hub.com/api/v1/process"
    SENTINEL_COLLECTION: str = "sentinel-2-l2a"
    SENTINEL_OUTPUT_SIZE: int = 512
    SPACENET_S3_BUCKET: str = "spacenet-dataset"
    SPACENET_SAMPLE_TIF_URL: str = ""


settings = Settings()
