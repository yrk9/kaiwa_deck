from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    database_url: str
    # APIを呼んでよいサイトのURL。複数ならカンマで区切る
    cors_origins: str = "http://localhost:3000"

    @property
    def cors_origin_list(self) -> list[str]:
        origins = self.cors_origins.split(",")
        return [o.strip() for o in origins if o.strip()]


settings = Settings()
