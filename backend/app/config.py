"""Application configuration loaded from environment variables."""
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    APP_NAME: str = "AI Trading Copilot"
    VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (defaults to SQLite async for zero-config local run; PostgreSQL supported via .env)
    DATABASE_URL: str = "sqlite+aiosqlite:///./trading_copilot.db"
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Seeding
    SEED_DEMO_DATA: bool = True

    # LLM Provider
    LLM_PROVIDER: str = "openai"  # openai | gemini
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # Risk Engine
    RISK_MAX_ORDER_VALUE: float = 500_000.0
    RISK_MAX_QUANTITY: int = 10_000
    RISK_MAX_DAILY_LOSS: float = -100_000.0
    RISK_MAX_POSITION_PCT: float = 0.40
    RISK_MAX_PRICE_DEVIATION: float = 0.20

    # Market Simulator
    MARKET_SEED: int = 42
    MARKET_TICK_INTERVAL: int = 30


settings = Settings()
