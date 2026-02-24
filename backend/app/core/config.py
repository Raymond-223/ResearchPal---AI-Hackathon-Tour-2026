from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ResearchPal MVP"
    cors_origins: str = "*"  # hackathon: allow all
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    
    # GenStudio API Configuration
    genstudio_api_key: str = ""
    genstudio_base_url: str = "https://api.genstudio.ai/v1"  # Default URL, can be overridden by env var

    class Config:
        env_file = ".env"


settings = Settings()