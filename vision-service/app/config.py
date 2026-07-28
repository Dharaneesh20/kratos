from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "vision-service"
    SERVICE_PORT: int = 8001

    DATA_DIR: str = "data"
    TRAIN_SAT_SUFFIX: str = "_sat.jpg"
    TRAIN_MASK_SUFFIX: str = "_mask.png"

    IMG_SIZE: int = 512
    MASK_THRESHOLD: int = 128

    WEIGHTS_DIR: str = "weights"
    MODEL_CHECKPOINT: str = "weights/roadnet.pt"
    ENCODER_NAME: str = "resnet34"

    class Config:
        env_file = ".env"


settings = Settings()
