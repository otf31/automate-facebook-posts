from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str

    admin_email: str
    admin_id: str
    admin_machine_id: str

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_dbname: str

    jwt_secret_key: str
    jwt_algorithm: str

    app_mode: str

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()  # type: ignore
