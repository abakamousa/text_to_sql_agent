from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from backend.utils.env_loader import load_env
import logging

# Ensure .env is loaded before Pydantic initializes
ENV_PATH = load_env(".env")

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    azure_openai_deployment: str = Field(..., env="AZURE_OPENAI_DEPLOYMENT")
    azure_openai_endpoint: str = Field(..., env="AZURE_OPENAI_ENDPOINT")
    azure_openai_api_key: str = Field(..., env="AZURE_OPENAI_API_KEY")
    azure_openai_api_version: str = Field("2024-06-01", env="AZURE_OPENAI_API_VERSION")
    sql_connection_string: str = Field(..., env="SQL_CONNECTION_STRING")
    appinsights_key: str | None = Field(None, env="APPINSIGHTS_KEY")
    environment: str = Field("development", env="ENVIRONMENT")

settings = Settings()
logging.info(f"✅ Settings initialized from: {ENV_PATH}")
