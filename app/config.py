from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "mysql+aiomysql://user:password@localhost:3306/support_tickets"
    api_key_user: str = "user-secret-key-here"
    api_key_admin: str = "admin-secret-key-here"
    upload_dir: str = "uploads"

    class Config:
        env_file = ".env"


settings = Settings()
