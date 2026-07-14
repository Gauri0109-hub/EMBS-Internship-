import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Determine absolute path to project root
CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DIR = os.path.dirname(CONFIG_DIR)
BACKEND_DIR = os.path.dirname(APP_DIR)
ROOT_DIR = os.path.dirname(BACKEND_DIR)

# Ensure local .env file is loaded from project root
dotenv_path = os.path.join(ROOT_DIR, ".env")
load_dotenv(dotenv_path=dotenv_path)

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///data/pharmacy_platform.db"
    JWT_SECRET: str = "8f9b23b3644f1db123e421cd756d1c9ef00192bc5c38c823ab23cd1cf0034a1b"
    JWT_REFRESH_SECRET: str = "7f5b34b8655f2db224e532cd867d2c9ef11202bc6c49c934ab34cd2cf1145a2c"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GEMINI_API_KEY: str = ""
    REDIS_URL: str = "redis://localhost:6379/0"
    ENV: str = "development"
    API_VERSION: str = "v1"

    model_config = SettingsConfigDict(
        env_file=dotenv_path,
        env_file_encoding='utf-8',
        extra="ignore"
    )

    def __init__(self, **values):
        super().__init__(**values)
        # Convert relative SQLite paths to absolute paths relative to ROOT_DIR
        if self.DATABASE_URL.startswith("sqlite:///"):
            path = self.DATABASE_URL.replace("sqlite:///", "")
            if not os.path.isabs(path):
                abs_path = os.path.abspath(os.path.join(ROOT_DIR, path))
                # Ensure the parent directory exists
                os.makedirs(os.path.dirname(abs_path), exist_ok=True)
                self.DATABASE_URL = f"sqlite:///{abs_path}"

settings = Settings()

