from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "ResearchPal MVP"
    cors_origins: str = "*"  # hackathon: allow all
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()