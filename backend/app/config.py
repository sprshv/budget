from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SECRET_KEY: str
    PLAID_CLIENT_ID: str
    PLAID_SECRET: str
    PLAID_ENV: str = "sandbox"
    ENCRYPTION_KEY: str
    FRONTEND_URL: str = "http://localhost:5173"
    APP_ENV: str = "development"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
