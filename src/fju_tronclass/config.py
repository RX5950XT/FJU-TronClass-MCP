"""應用程式設定：從 .env 或環境變數讀取，型別安全。"""

from __future__ import annotations

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全域設定。優先順序：環境變數 > .env 檔 > 預設值。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # TronClass 連線設定
    tronclass_base_url: str = "https://elearn2.fju.edu.tw"
    tronclass_session_cookie: str = ""

    # 工具行為
    fjumcp_download_dir: Path = Path.home() / "Downloads" / "TronClass"
    fjumcp_log_level: str = "INFO"

    @field_validator("fjumcp_log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log level 必須是 {allowed} 之一，得到 {v!r}")
        return upper

    @field_validator("tronclass_base_url")
    @classmethod
    def strip_trailing_slash(cls, v: str) -> str:
        return v.rstrip("/")


def get_settings() -> Settings:
    """取得設定實例（每次呼叫都會重新讀取，便於測試中 monkeypatch）。"""
    return Settings()
