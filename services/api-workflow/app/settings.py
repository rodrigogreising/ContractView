from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql://contractview:contractview@localhost:5432/contractview"
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "contractview"
    minio_secret_key: str = "contractview-demo-secret"
    minio_bucket: str = "contractview-artifacts"
    minio_secure: bool = False
    session_secret: str = "local-synthetic-poc-only"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
