from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central settings loaded from environment or .env file."""

    # Azure OpenAI
    azure_openai_deployment: str
    azure_openai_endpoint: str
    azure_openai_api_version: str = "2024-06-01"

    # Azure SQL
    sql_connection_string: str | None = None  # or use Key Vault

    # Azure Monitoring
    appinsights_key: str | None = None

    # General
    environment: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Singleton-style accessor
settings = Settings()
