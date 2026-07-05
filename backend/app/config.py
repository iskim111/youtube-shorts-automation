from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILES = (
    str(_PROJECT_ROOT / ".env"),
    str(_PROJECT_ROOT / "backend" / ".env"),
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    create_tables_on_startup: bool = True
    app_name: str = "shorts-automation"
    default_operation_mode: Literal["manual", "semi_auto", "auto"] = "semi_auto"
    daily_upload_cap: int = 5
    default_publish_hours: str = "18,19,20,21"

    database_url: str = "sqlite+aiosqlite:///./data/shorts.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "amqp://shorts:shorts@localhost:5672//"
    celery_result_backend: str = "redis://localhost:6379/1"

    storage_backend: Literal["minio", "gcs"] = "minio"
    storage_endpoint: str = "http://localhost:9000"
    storage_access_key: str = "minioadmin"
    storage_secret_key: str = "minioadmin"
    storage_bucket: str = "shorts-assets"
    storage_region: str = "us-east-1"

    jwt_secret: str = "change-me-in-production"
    jwt_access_expire_min: int = 15
    jwt_refresh_expire_days: int = 7

    frontend_port: int = 3001
    cors_origins: str = "http://localhost:3001"
    frontend_base_url: str = "http://localhost:3001"

    # YouTube OAuth
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8000/api/v1/channels/oauth/callback"
    youtube_scopes: str = (
        "openid,"
        "https://www.googleapis.com/auth/userinfo.email,"
        "https://www.googleapis.com/auth/userinfo.profile,"
        "https://www.googleapis.com/auth/youtube.upload,"
        "https://www.googleapis.com/auth/youtube.readonly"
    )

    # Category allowlist (Phase 1)
    category_allowlist: list[str] = ["comedy", "food", "daily_pet", "tips"]
    max_video_duration_sec: int = 45
    data_dir: str = "./data"
    ffmpeg_path: str = ""
    pilot_dry_run_upload: bool = True
    pilot_default_privacy: Literal["private", "unlisted", "public"] = "private"
    use_celery: bool = False

    # Stock & AI asset APIs
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
    openai_api_key: str = ""
    youtube_api_key: str = ""
    elevenlabs_api_key: str = ""
    heygen_api_key: str = ""
    gcp_project_id: str = ""
    asset_strategy: Literal["free_only", "hybrid", "ai_preferred"] = "free_only"
    video_mode: Literal["ai_character", "stock_broll"] = "ai_character"
    trending_cache_ttl_hours: int = 6
    ai_image_provider: Literal["openai", "none"] = "openai"
    ai_video_provider: Literal["none", "runway", "luma"] = "none"
    runway_api_key: str = ""
    luma_api_key: str = ""
    ai_max_scenes_per_job: int = 1
    slack_webhook_url: str = ""
    auth_enabled: bool = False
    admin_email: str = "admin@localhost"
    admin_password: str = "admin1234"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def publish_hour_list(self) -> list[int]:
        return [int(h.strip()) for h in self.default_publish_hours.split(",") if h.strip()]

    @property
    def youtube_scope_list(self) -> list[str]:
        return [s.strip() for s in self.youtube_scopes.split(",") if s.strip()]

    @property
    def youtube_configured(self) -> bool:
        return bool(self.youtube_client_id and self.youtube_client_secret)

    @property
    def ai_image_configured(self) -> bool:
        return self.ai_image_provider == "openai" and bool(self.openai_api_key)

    @property
    def ai_video_configured(self) -> bool:
        if getattr(self, "heygen_api_key", ""):
            return True
        if self.ai_video_provider == "runway":
            return bool(self.runway_api_key)
        if self.ai_video_provider == "luma":
            return bool(self.luma_api_key)
        return False

    @property
    def elevenlabs_configured(self) -> bool:
        return bool(getattr(self, "elevenlabs_api_key", ""))

    @property
    def heygen_configured(self) -> bool:
        return bool(getattr(self, "heygen_api_key", ""))

    @property
    def youtube_data_configured(self) -> bool:
        return bool(getattr(self, "youtube_api_key", ""))

    @property
    def stock_configured(self) -> bool:
        return bool(self.pexels_api_key or self.pixabay_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
