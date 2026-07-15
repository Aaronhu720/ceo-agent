from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = "CEO Agent"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "change-me"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "ceoagent"
    POSTGRES_PASSWORD: str = "ceoagent_dev_password"
    POSTGRES_DB: str = "ceoagent"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL_SYNC(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    @property
    def REDIS_URL(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/0"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    JWT_SECRET_KEY: str = "change-me-jwt"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    STORAGE_PROVIDER: str = "minio"
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "ceoagent"
    STORAGE_REGION: str = "ap-southeast-1"
    STORAGE_PUBLIC_URL: str = "http://localhost:9000/ceoagent"

    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OPENAI_DEFAULT_MODEL: str = "gpt-4o"

    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_DEFAULT_MODEL: str = "claude-sonnet-4-20250514"

    GEMINI_API_KEY: str = ""
    GEMINI_DEFAULT_MODEL: str = "gemini-2.0-flash"

    DEFAULT_MODEL_PROVIDER: str = "openai"

    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    CORS_ORIGINS: str = "http://localhost:3000"
    RATE_LIMIT_PER_MINUTE: int = 60
    MAX_FILE_SIZE_MB: int = 100
    DEFAULT_TIMEZONE: str = "Asia/Singapore"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
