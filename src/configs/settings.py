from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB_URL: str
    REDIS_HOST: str
    REDIS_PORT: int

    JWT_PRIVATE_KEY_FILE_PATH: str
    JWT_PUBLIC_KEY_FILE_PATH: str
    JWT_ALGORITHM: str
    JWT_ACCESS_EXPIRATION_IN_SECONDS: int
    JWT_REFRESH_EXPIRATION_IN_SECONDS: int
    JWT_ISSUER: str
    JWT_AUDIENCE: str
    JWT_REDIS_PREFIX: str
    JWT_LEEWAY_IN_SECONDS: int

    SALT: str
    PASSWORD_HASH_LENGTH: int
    PASSWORD_SALT_LENGTH: int

# we will load values from environment variables at runtime
app_settings = Settings()  # type: ignore[call-arg]
