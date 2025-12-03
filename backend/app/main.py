from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException
from jwt import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from sqlmodel import select
from starlette import status

from .config import settings
from .database import SessionDep
from .models import RoleEnum, User
from .security import verify_password
from .startup import create_super_admin_user


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa
    # This function will be called when the app starts up
    # Create admin user if it doesn't exist
    create_super_admin_user()

    yield


if settings.env == "production":
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
else:
    app = FastAPI(lifespan=lifespan)


def authenticate_super_admin(super_admin: User, password: str):
    """
    Authenticate a super admin user
    """
    if not super_admin:
        return False

    if super_admin.role != RoleEnum.super_admin:
        return False

    if not verify_password(password, super_admin.password):
        return False

    return super_admin


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


class UserCreateUpdate(BaseModel):
    super_admin_id: str
    super_admin_password: str
    machine_id: str
    user_id: str
    days: int = 0
    hours: int = 0
    minutes: int
    comment: str | None = None


@app.post("/register-update")
def register_update(payload: UserCreateUpdate, session: SessionDep) -> User:
    """
    Endpoint to create or update a user based on the machine_id and a time delta
    This endpoint will create or update the user's jwt token
    :param payload: Body of the request
    :param session: SessionDep dependency
    :return: A user object or an HTTPException
    """
    # Check if the user exists
    super_admin = session.exec(
        select(User).where(User.user_id == payload.super_admin_id)
    ).first()
    user = session.exec(
        select(User).where(User.machine_id == payload.machine_id)
    ).first()

    if not (authenticate_super_admin(super_admin, payload.super_admin_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="только для Денис",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If the user exists then update the jwt, otherwise create a new user with the jwt
    if not user:
        user = User(user_id=payload.user_id, machine_id=payload.machine_id)

    # Save the previous jwt token
    previous_jwt = user.jwt

    jwt_payload = {
        "sub": str(user.id),
        "user_id": user.user_id,
        "machine_id": user.machine_id,
        "iat": datetime.now(timezone.utc),
    }

    # Create a new jwt token
    access_token_expires = timedelta(
        days=payload.days, hours=payload.hours, minutes=payload.minutes
    )
    access_token = create_access_token(
        data=jwt_payload, expires_delta=access_token_expires
    )

    # Update the user object
    user.comment = payload.comment
    user.jwt = access_token
    user.previous_jwt = previous_jwt

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@app.get("/check-subscription")
def check_subscription(machine_id: str, session: SessionDep) -> str | None:
    def raise_error(detail):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    # If the user does not exist
    if not (
        user := session.exec(select(User).where(User.machine_id == machine_id)).first()  # noqa
    ):
        raise_error("User not found.")

    # If the user is disabled
    if user.is_disabled:
        raise_error("Disabled.")

    # If the user does not have a jwt token
    if not user.jwt:
        raise_error("No subscription.")

    try:
        jwt.decode(
            user.jwt,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp", "iat"]},
        )

        return user.machine_id
    except ExpiredSignatureError:
        raise_error("Subscription expired")
    except InvalidTokenError:
        raise_error("Could not validate credentials")


@app.get("/health")
def get_status():
    return {"status": "ok"}
