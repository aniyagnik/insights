from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "Real-Time Analytics Platform"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "local"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/analytics"
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()