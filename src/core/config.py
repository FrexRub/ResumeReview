import logging
from pathlib import Path

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent
REFRESH_COOKIE_NAME = "resume_review_refresh"


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        datefmt="%Y-%m-%d %H:%M:%S",
        format="[%(asctime)s.%(msecs)03d] %(module)10s:%(lineno)-3d %(levelname)-7s - %(message)s",
    )


class DbSetting(BaseSettings):
    postgres_user: str = "test"
    postgres_password: str = "test"
    postgres_db: str = "testdb"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    echo: bool = False

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore"
    )

    @property
    def url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore"
    )

    @property
    def url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class AuthJWT(BaseModel):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_minutes: int = 60 * 24 * 7


class Setting(BaseSettings):
    db: DbSetting = DbSetting()
    redis: RedisSettings = RedisSettings()
    auth_jwt: AuthJWT = AuthJWT()
    secret_key: SecretStr = "change-me-in-production"
    frontend_url: str = "http://localhost:5173"
    cookie_secure: bool = False
    parserdoc_url: str = "https://parserdoc.srubai.ru"
    parserdoc_timeout_seconds: int = 120
    max_upload_bytes: int = 20 * 1024 * 1024
    yandex_disk_oauth_token: SecretStr = ""
    yandex_disk_api_url: str = "https://cloud-api.yandex.net"
    yandex_disk_timeout_seconds: int = 120

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore"
    )

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.frontend_url.split(",")
            if origin.strip()
        ]


setting = Setting()
