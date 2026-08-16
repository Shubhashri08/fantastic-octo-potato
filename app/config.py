from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/vigrah_l5")
    TEST_DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@localhost:5432/vigrah_l5_test")

    # JWT Security Configuration
    JWT_SECRET: str = Field(default="super_secret_signing_key_change_me_in_production_1234567890")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # Google GenAI Configuration
    GEMINI_API_KEY: str = Field(default="mock_key_for_testing")
    GEMINI_MODEL: str = Field(default="gemini-1.5-flash")

    # Bootstrapping Admin Configuration
    BOOTSTRAP_ADMIN_USER: str = Field(default="admin")
    BOOTSTRAP_ADMIN_PASSWORD: str = Field(default="VigrahAdminPassword2026!")

    # Integration settings for upstream Layers 3 and 4
    LAYER3_BASE_URL: str = Field(default="http://localhost:8003")
    LAYER3_CLIENT_TOKEN: str = Field(default="layer3_secret_token_abc123")
    LAYER4_BASE_URL: str = Field(default="http://localhost:8004")
    LAYER4_CLIENT_TOKEN: str = Field(default="layer4_secret_token_xyz789")

    # Network timeouts for connections
    INTEGRATION_TIMEOUT_SECONDS: float = Field(default=5.0)

    # Distance tolerance for context verification (lat/long degrees)
    GEOGRAPHIC_TOLERANCE: float = Field(default=0.001)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
