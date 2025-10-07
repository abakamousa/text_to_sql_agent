from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Central settings loaded from environment or .env file."""

    # Azure OpenAI
    azure_openai_deployment: str | None = Field(default=None)
    azure_openai_endpoint: str | None = Field(default=None)
    azure_openai_api_key: str | None = Field(default=None)
    azure_openai_api_version: str = "2024-06-01"

    # Azure SQL
    sql_connection_string: str | None = Field(default=None)

    # Azure Monitoring
    appinsights_key: str | None = None
    

    # General
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


# Singleton-style accessor
settings = Settings()
