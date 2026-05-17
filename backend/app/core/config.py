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
    redis_url: str = "redis://localhost:6379/0"
    session_ttl_seconds: int = 2_592_000
    llm_provider: str = "ollama"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"
    ollama_fallback_model: str = "qwen2.5:7b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_api_key: str | None = None
    groq_chat_model: str = "llama-3.3-70b-versatile"
    groq_fallback_model: str = "llama-3.1-8b-instant"
    agent_temperature: float = 0.1
    agent_max_tokens: int = 512
    agent_json_repair_retries: int = 1
    agent_max_questions_before_result: int = 8
    agent_timeout_seconds: int = 20
    voice_provider: str = "local"
    asr_min_confidence: float = 0.70
    voice_max_utterance_seconds: int = 20
    voice_max_upload_mb: int = 8
    browser_asr_fallback_after_ms: int = 2000
    groq_whisper_model: str = "whisper-large-v3-turbo"
    groq_audio_transcriptions_url: str | None = None
    whisper_cpp_binary: str = "/opt/whisper.cpp/build/bin/whisper-cli"
    whisper_cpp_model_path: str = "/models/ggml-large-v3.bin"
    whisper_cpp_args: str = "-l auto -otxt -ojf --print-progress false --no-timestamps"
    asr_timeout_seconds: int = 12
    translation_provider: str = "local_indictrans2"
    translation_service_url: str = "http://localhost:8001"
    ai4bharat_translate_url: str | None = None
    ai4bharat_api_key: str | None = None
    ai4bharat_timeout_seconds: int = 3
    google_translate_api_key: str | None = None
    google_translate_url: str = "https://translation.googleapis.com/language/translate/v2"
    tts_provider: str = "local_indictts"
    local_tts_url: str = "http://localhost:8002"
    local_tts_timeout_seconds: int = 8
    google_tts_url: str = "https://texttospeech.googleapis.com/v1/text:synthesize"
    google_application_credentials: str | None = None
    tts_cache_ttl_seconds: int = 86_400
    translation_cache_ttl_seconds: int = 604_800
    store_audio_debug: bool = False
    auth_jwt_secret: str = "change-me-phase-4"
    auth_cookie_secure: bool = True
    auth_cookie_name: str = "adhikarai_session"
    auth_jwt_ttl_seconds: int = 2_592_000
    otp_provider: str = "mock"
    otp_expiry_seconds: int = 300
    otp_retry_after_seconds: int = 30
    otp_max_attempts: int = 5
    msg91_base_url: str = "https://control.msg91.com/api/v5"
    msg91_auth_key: str | None = None
    msg91_template_id: str | None = None
    vapid_public_key: str | None = None
    vapid_private_key: str | None = None
    dashboard_enabled: bool = True
    dashboard_session_idle_timeout_seconds: int = 3600
    rate_limit_user_per_day: int = 100
    rate_limit_operator_per_day: int = 1000
    rate_limit_guest_per_day: int = 50
    export_storage_provider: str = "local"
    export_max_rows: int = 5000
    bulk_eligibility_max_rows: int = 500
    bulk_eligibility_max_mb: int = 2
    sms_notifications_enabled: bool = False
    msg91_sms_template_id: str | None = None
    quality_monitor_cron: str = "0 * * * *"
    scheme_expiry_warning_days: int = 30

    @property
    def groq_transcriptions_url(self) -> str:
        return self.groq_audio_transcriptions_url or f"{self.groq_base_url.rstrip('/')}/audio/transcriptions"


@lru_cache
def get_settings() -> Settings:
    return Settings()
