from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"
    app_timezone: str = "Asia/Kolkata"
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    database_url: str = "postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai"
    database_direct_url: str = "postgresql+asyncpg://adhikarai:adhikarai@localhost:5432/adhikarai"
    db_pool_size: int = 3
    db_max_overflow: int = 2
    db_pool_timeout: int = 10
    db_pool_recycle: int = 300
    admin_api_token: str = "change-me"
    eligibility_engine: str = "experta"
    embedding_provider: str = "sentence_transformers"
    embedding_model: str = "intfloat/multilingual-e5-small"
    faiss_index_dir: str = "./data/faiss"
    enable_scheduler: bool = True
    expiry_check_cron: str = "0 2 * * *"
    myscheme_api_base_url: str | None = None
    myscheme_api_token: str | None = None
    myscheme_ingestion_mode: str = "json_file"
    ingestion_auto_publish: bool = False
    test_database_url: str | None = Field(default=None)


@lru_cache
def get_settings() -> Settings:
    return Settings()

