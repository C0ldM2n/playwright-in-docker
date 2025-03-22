from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CHANNEL: Literal["chrome", "chromium"] = "chrome"
    HEADLESS: bool = False
    PASSWORD: str | int = "eight_digits"

    METAMASK_VERSION: str = "12.14.0"

    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )


settings = Settings()
