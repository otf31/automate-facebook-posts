from datetime import datetime, timedelta, timezone

import jwt
from fastapi import FastAPI, HTTPException
from jwt import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel
from sqlmodel import select
from starlette import status

from config import settings
from database import SessionDep
from models import User

app_mode = settings.app_mode

if app_mode == "production":
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
else:
    app = FastAPI()


def authenticate_user(user: User):
    if not user:
        return False

    if user.role != "super_admin":
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + expires_delta

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


class UserCreateUpdate(BaseModel):
    superadmin_machine_id: str
    machine_id: str
    user_id: str
    days: int = 0
    minutes: int = 0
    seconds: int


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
    super_user = session.exec(
        select(User).where(User.machine_id == payload.superadmin_machine_id)  # noqa
    ).first()
    user = session.exec(
        select(User).where(User.machine_id == payload.machine_id)  # noqa
    ).first()

    superadmin = authenticate_user(super_user)

    if not superadmin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="только для Денис",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # If the user exists update the jwt, otherwise create a new user with the jwt
    if not user:
        user = User(
            machine_id=payload.machine_id,
            user_id=payload.user_id,
        )

    # Save the previous jwt token
    previous_jwt = user.jwt

    jwt_payload = {
        "sub": user.machine_id,
        "iat": datetime.now(timezone.utc),
    }

    # Create a new jwt token
    access_token_expires = timedelta(
        days=payload.days, minutes=payload.minutes, seconds=payload.seconds
    )
    access_token = create_access_token(
        data=jwt_payload, expires_delta=access_token_expires
    )

    user.jwt = access_token
    user.previous_jwt = previous_jwt

    session.add(user)
    session.commit()
    session.refresh(user)

    return user


@app.get("/check-subscription")
def check_subcscription(machine_id: str, session: SessionDep) -> str | None:
    def raise_error(detail):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    user = session.exec(select(User).where(User.machine_id == machine_id)).first()  # noqa

    # If the user does not exist
    if not user:
        raise_error("User not found")

    # If the user is disabled
    if user.disabled:
        raise_error("Disabled")

    # If the user does not have a jwt token
    if not user.jwt:
        raise_error("No subscription")

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


@app.get("/status")
def get_status():
    return {"status": "ok"}
