from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str

    super_admin_email: str
    super_admin_id: str

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_dbname: str

    jwt_secret_key: str
    jwt_algorithm: str

    env: str

    model_config = SettingsConfigDict(env_file=[".env", ".env.prod"])


settings = Settings()
