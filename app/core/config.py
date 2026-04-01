from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://booking:booking@localhost:5434/booking"
    debug: bool = False  

    model_config = {"env_file": ".env"}


settings = Settings()