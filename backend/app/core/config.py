from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    database_url: str


settings = Settings()
