import logging
from pathlib import Path

from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).parent.parent.parent

COOKIE_NAME = "bonds_resume"
CACHE_EXP = 3600

api_key_header = APIKeyHeader(name="Authorization", auto_error=False)


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

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")

    @property
    def url(self):
        res: str = (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}"
            f"/{self.postgres_db}"
        )
        return res


class RedisSettings(BaseSettings):
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")

    @property
    def url(self):
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


class AuthJWT(BaseModel):
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7


class Setting(BaseSettings):
    db: DbSetting = DbSetting()
    redis: RedisSettings = RedisSettings()
    auth_jwt: AuthJWT = AuthJWT()
    secret_key: SecretStr = "test"
    templates_dir: str = "templates"
    frontend_url: str = "test"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", env_file_encoding="utf8", extra="ignore")


setting = Setting()
