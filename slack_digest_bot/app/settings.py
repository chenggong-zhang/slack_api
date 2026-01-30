from functools import lru_cache
from typing import List, Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Slack
    slack_bot_token: SecretStr = SecretStr("dev-slack-bot-token")
    slack_app_token: Optional[SecretStr] = None  # Required for Socket Mode
    slack_signing_secret: Optional[SecretStr] = None
    slack_client_id: Optional[str] = None
    slack_client_secret: Optional[SecretStr] = None
    slack_scopes: List[str] = Field(default_factory=list)

    # OpenAI
    openai_api_key: SecretStr = SecretStr("dev-openai-key")
    openai_model_digest: str = "gpt-4.1"
    openai_model_nl: str = "gpt-4.1-mini"

    # Database
    database_url: str = "sqlite:///./slack_digest.db"
    app_encryption_key: SecretStr = SecretStr("dev-encryption-key-please-change")
    message_retention_days: int = 30

    # Scheduling
    default_digest_hour_local: int = 9
    default_digest_minute_local: int = 0

    # Runtime
    log_level: str = "INFO"
    env: str = "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()
