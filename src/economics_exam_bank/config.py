from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# 專案根目錄 Projects/economics-exam-bank
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = BASE_DIR / "economics_exam.db"


class Settings(BaseSettings):
    PROJECT_NAME: str = "經濟學研究所考試題庫 API"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{DEFAULT_DB_PATH.as_posix()}"
    CORS_ORIGINS: list[str] = ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
