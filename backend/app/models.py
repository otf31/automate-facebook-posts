from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        sa_column=sa.Column(sa.UUID(as_uuid=True), primary_key=True),
    )
    machine_id: str = Field(index=True, unique=True)
    jwt: str | None = Field(default=None)
    previous_jwt: str | None = Field(default=None)
    comment: str | None = Field(default=None)
    is_disabled: bool = Field(default=False)


class Admin(SQLModel, table=True):
    __tablename__ = "admin"

    admin_id: str = Field(unique=True, primary_key=True)
    password: str = Field()
