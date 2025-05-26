from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DB_NAME: str = "talentbridge"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "admin"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # Application
    APP_NAME: str = "TalentBridge API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore les champs supplémentaires du .env


settings = Settings()