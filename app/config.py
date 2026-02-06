from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # Meta/Facebook
    FACEBOOK_APP_ID: str
    FACEBOOK_APP_SECRET: str
    REDIRECT_URI: str = "http://localhost:8000/auth/callback"

    # Application
    API_BASE_URL: str = "http://localhost:8000"

settings = Settings()