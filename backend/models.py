from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    machine_id: str = Field(index=True)
    user_id: str | None = Field(default=None)
    jwt: str | None = Field(default=None)
    previous_jwt: str | None = Field(default=None)
    role: str | None = Field(default=None)
    disabled: bool | None = Field(default=False)
    comment: str | None = Field(default=None)
