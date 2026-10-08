from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "LearnGraph API"
    app_version: str = "0.1.0"
    debug: bool = True
    database_url: str
    ollama_base_url: str = "https://localhost:11434"
    ollama_model: str = "qwen2.5.3b"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()