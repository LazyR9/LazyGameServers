from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.management.upgrades import CURRENT_VERSION

"""
NOTE: If a new config is added or an old one removed you don't need to bump the version.
Any new fields will just use their default values, and old ones will be ignored,
and both will be updated the next time the config saves.

The only time a version bump is needed is when a config value is moved/renamed,
so that the new value can get set from the old one.
"""

class Config(BaseModel):
    class_map: dict[str, str] = {}

    password_hash: str | None = None
    setup: bool = False

    version: int = CURRENT_VERSION


class EnvConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="LGS_", env_file=".env", extra="ignore")
    
    TOKEN_SECRET: str = "dev secret"
