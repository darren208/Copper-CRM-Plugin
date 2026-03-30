from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development")
    app_base_url: str = Field(default="http://localhost:8080")
    app_version: str = Field(default="1.0.0")

    # Database
    database_url: str = Field(
        default="postgresql+psycopg://user:password@localhost:5432/copper_crm_plugin"
    )

    # Google Cloud
    google_cloud_project: str = Field(default="")
    google_cloud_region: str = Field(default="us-central1")
    gcs_bucket: str = Field(default="")
    pubsub_topic_events: str = Field(default="copper-crm-events")
    pubsub_subscription_events: str = Field(default="copper-crm-events-sub")

    # RingCentral
    ringcentral_client_id: str = Field(default="")
    ringcentral_client_secret: str = Field(default="")
    ringcentral_server_url: str = Field(default="https://platform.ringcentral.com")
    ringcentral_webhook_validation_token: str = Field(default="")
    ringcentral_jwt: str = Field(default="")

    # Copper CRM
    copper_client_id: str = Field(default="")
    copper_client_secret: str = Field(default="")
    copper_redirect_uri: str = Field(default="")
    copper_api_base_url: str = Field(default="https://api.copper.com/developer_api/v1")

    # OpenAI
    openai_api_key: str = Field(default="")
    openai_model: str = Field(default="gpt-4o")

    # Vertex AI / Gemini
    vertex_model: str = Field(default="gemini-1.5-pro")

    # JWT Auth
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=480)

    # CORS
    cors_origins: list[str] = Field(
        default=[
            "https://app.copper.com",
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )

    # Worker settings
    pubsub_max_messages: int = Field(default=10)
    pubsub_ack_deadline_seconds: int = Field(default=60)

    # Retention
    transcript_retention_days: int = Field(default=30)
    audio_retention_days: int = Field(default=30)

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
