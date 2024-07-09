from typing_extensions import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Depends
from functools import lru_cache

class Settings(BaseSettings):

    gh_api_token: str

    sql_db_url: str

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.production"),
        env_file_encoding="utf-8",
        extra="allow"
    )

@lru_cache
def get_settings():
    return Settings()

settings = Annotated[Settings, Depends(get_settings)]