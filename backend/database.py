from typing import Annotated

from fastapi import Depends
from sqlalchemy import NullPool
from sqlmodel import create_engine, Session

from config import settings

USER = settings.postgres_user
PASSWORD = settings.postgres_password
HOST = settings.postgres_host
PORT = settings.postgres_port
DBNAME = settings.postgres_dbname

DATABASE_URL = (
    f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
engine = create_engine(DATABASE_URL, poolclass=NullPool)
