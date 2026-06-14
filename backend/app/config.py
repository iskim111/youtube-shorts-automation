from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

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

    cors_origins: str = "http://localhost:3000"
    frontend_base_url: str = "http://localhost:3000"

    # YouTube OAuth
    youtube_client_id: str = ""
    youtube_client_secret: str = ""
    youtube_redirect_uri: str = "http://localhost:8000/api/v1/channels/oauth/callback"
    youtube_scopes: str = (
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

    # Stock APIs (Beta)
    pexels_api_key: str = ""
    pixabay_api_key: str = ""
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
