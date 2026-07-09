from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "FastAPI User Service"
    debug: bool = False

    secret_key: str = "change-me"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql://user:password@localhost:5432/users"

    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-southeast-1"
    s3_bucket_name: str = ""
    # Optional: set for MinIO / LocalStack (leave empty for real AWS S3)
    s3_endpoint_url: str | None = None
    s3_public_endpoint_url: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
