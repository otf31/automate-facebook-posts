from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from jwt import ExpiredSignatureError
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel, Field, field_validator
from sqlmodel import select
from starlette import status
from starlette.responses import JSONResponse

from .config import settings
from .database import SessionDep
from .models import Admin, User
from .security import get_password_hash, verify_password
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError):
    sanitized_errors = []

    for err in exc.errors():
        sanitized_errors.append(
            {
                "loc": err.get("loc"),
                "msg": err.get("msg"),
                "type": err.get("type"),
                # ❌ DO NOT include "input"
            }
        )

    return JSONResponse(status_code=422, content={"detail": sanitized_errors})


def authenticate_super_admin(super_admin: Admin, admin_id: str, password: str) -> bool:
    """
    Authenticate a super admin user
    """
    if admin_id != super_admin.admin_id:
        return False

    if not verify_password(password, super_admin.password):
        return False

    return True


def create_access_token(data: dict, expires_on: date):
    to_encode = data.copy()

    to_encode.update(
        {
            "exp": datetime(
                expires_on.year,
                expires_on.month,
                expires_on.day,
                23,
                59,
                59,
                tzinfo=ZoneInfo("America/Lima"),
            )
        }
    )

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )

    return encoded_jwt


class SuperAdminPasswordUpdate(BaseModel):
    previous_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)


class UserCreateUpdate(BaseModel):
    super_admin_id: str = Field(min_length=1)
    super_admin_password: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    expires_on: date = Field()
    comment: str | None = None

    @field_validator("expires_on")
    @classmethod
    def must_be_future(cls, value):
        if datetime(
            value.year,
            value.month,
            value.day,
            23,
            59,
            59,
            tzinfo=ZoneInfo("America/Lima"),
        ) <= datetime.now(timezone.utc):
            raise ValueError("Date must be in the future")

        return value


def auth_super_admin(
    payload: UserCreateUpdate,
    session: SessionDep,
):
    super_admin = session.exec(select(Admin)).first()

    if not (
        authenticate_super_admin(
            super_admin, payload.super_admin_id, payload.super_admin_password
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="только для Денис",
            headers={"WWW-Authenticate": "Bearer"},
        )


@app.post("/change-super-admin-password")
def change_super_admin_password(payload: SuperAdminPasswordUpdate, session: SessionDep):
    """
    Change super admin password
    :param payload: Body of the request
    :param session: SessionDep dependency
    :return: An HTTP response
    """
    super_admin = session.exec(select(Admin)).first()

    if verify_password(payload.previous_password, super_admin.password):
        super_admin.password = get_password_hash(payload.new_password)

        session.add(super_admin)
        session.commit()

        return Response(status_code=status.HTTP_204_NO_CONTENT)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="только для Денис",
        headers={"WWW-Authenticate": "Bearer"},
    )


@app.post("/register-update", dependencies=[Depends(auth_super_admin)])
def register_update(
    payload: UserCreateUpdate,
    session: SessionDep,
) -> User:
    """
    Endpoint to create or update a user based on the machine_id and a time delta
    This endpoint will create or update the user's jwt token
    :param payload: Body of the request
    :param session: SessionDep dependency
    :return: A user object or an HTTPException
    """
    user = session.exec(
        select(User).where(User.machine_id == payload.machine_id)
    ).first()

    # If the user exists then update the jwt, otherwise create a new user with the jwt
    if not user:
        user = User(machine_id=payload.machine_id)

    # Save the previous jwt token
    previous_jwt = user.jwt

    jwt_payload = {
        "sub": user.machine_id,
        "iat": datetime.now(timezone.utc),
        "comment": user.comment,
    }

    # Create a new jwt token
    access_token = create_access_token(data=jwt_payload, expires_on=payload.expires_on)

    # Update the user object
    user.jwt = access_token
    user.previous_jwt = previous_jwt

    if payload.comment:
        user.comment = payload.comment

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

        return user.jwt
    except ExpiredSignatureError:
        raise_error("Subscription expired")
    except InvalidTokenError:
        raise_error("Could not validate credentials")


@app.get("/health")
def get_status():
    return {"status": "ok"}
