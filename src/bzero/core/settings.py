"""
Application Settings - Pydantic Settings를 사용한 환경 변수 관리.

환경 변수를 로드하고 검증하며, 애플리케이션 전역 설정을 제공합니다.
"""

from enum import Enum
from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """실행 환경을 나타내는 enum; test, local, development, production."""

    TEST = "test"
    LOCAL = "local"
    DEVELOPMENT = "development"
    PRODUCTION = "production"


class LogSettings(BaseModel):
    level: str = "INFO"
    dir: str = "logs"
    file_max_bytes: int = 10485760
    file_backup_count: int = 5


class DatabaseSettings(BaseModel):
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: SecretStr = SecretStr("")
    db: str = "postgres"

    @property
    def async_url(self) -> str:
        """비동기 PostgreSQL 데이터베이스 URL을 반환합니다 (FastAPI용)."""
        return f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"

    @property
    def sync_url(self) -> str:
        """동기 PostgreSQL 데이터베이스 URL을 반환합니다 (Celery용)."""
        return f"postgresql+psycopg://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.db}"


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: SecretStr = SecretStr("")

    @property
    def url(self) -> str:
        return f"redis://:{self.password.get_secret_value()}@{self.host}:{self.port}/0"


class CorsSettings(BaseModel):
    origins: list[str] = ["http://localhost:5173"]
    allow_methods: list[str] = ["*"]
    allow_headers: list[str] = ["*"]
    allow_credentials: bool = True


class AuthSettings(BaseModel):
    """Supabase JWT 인증 설정"""

    supabase_jwt_secret: SecretStr = SecretStr("default-jwt-secret-replace-in-production")
    jwt_algorithm: str = "HS256"


class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/1"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
        env_nested_delimiter="__",
    )
    """애플리케이션의 전체 설정을 관리하는 클래스."""

    app_name: str = "B0 API"
    app_version: str = "0.0.1"

    environment: Environment = Environment.LOCAL

    log: LogSettings = LogSettings()
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    cors: CorsSettings = CorsSettings()
    auth: AuthSettings = AuthSettings()
    celery: CelerySettings = CelerySettings()

    timezone: ZoneInfo = ZoneInfo("Asia/Seoul")

    @property
    def is_debug(self) -> bool:
        return self.environment not in (Environment.TEST, Environment.PRODUCTION)


@lru_cache
def get_settings() -> Settings:
    return Settings()
