from pydantic import (
    AliasChoices,
    Field,
    PostgresDsn,
    RedisDsn,
)

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # db
    redis_dsn: RedisDsn = Field(
        "redis://user:pass@localhost:6379/1",
        validation_alias=AliasChoices("redis_dsn", "service_redis_dsn", "redis_url"),
    )
    pg_dsn: PostgresDsn = Field("postgresql+asyncpg://user:pass@localhost:5432/foobar")

    # jaeger
    jaeger_endpoint: str = Field("http://jaeger:4317")

    # jwt
    jwt_secret_key: str = Field("secret")
    jwt_access_expire_minutes: int = Field(15)
    jwt_refresh_expire_days: int = Field(7)


settings = Settings()
