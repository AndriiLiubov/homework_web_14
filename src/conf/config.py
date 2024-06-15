from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PG_DB: str
    PG_USER: str
    PG_PASSWORD: str
    PG_PORT: int
    PG_DOMAIN: str

    DB_URL: str
    SECRET_KEY_JWT: str
    ALGORITHM: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str

    REDIS_DOMAIN: str
    REDIS_PORT: int
    REDIS_PASSWORD: str

    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()