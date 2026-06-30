from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    app_name: str = Field(default="Ferramenta de avaliação da cultura organizacional API", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="APP_DEBUG")
    database_url: str = Field(alias="DATABASE_URL")
    allowed_origins_raw: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        alias="ALLOWED_ORIGINS",
    )
    admin_email: str = Field(default="admin@sistema.com", alias="ADMIN_EMAIL")
    admin_password: str = Field(default="wPFOmTE1TEW9#oUE", alias="ADMIN_PASSWORD")

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.allowed_origins_raw.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
