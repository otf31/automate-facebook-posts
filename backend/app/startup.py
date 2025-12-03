from sqlmodel import Session, select

from .config import settings
from .database import engine
from .models import RoleEnum, User
from .security import get_password_hash


def create_super_admin_user():
    with Session(engine) as session:
        existing_super_admin = session.exec(
            select(User).where(User.role == RoleEnum.super_admin)  # noqa
        ).first()

        if existing_super_admin:
            print("Super admin user already exists.")
            return

        super_admin = User(
            user_id=settings.super_admin_id,
            password=get_password_hash(settings.super_admin_password),
            machine_id=settings.super_admin_machine_id,
            role=RoleEnum.super_admin,
            comment="Мой компутер",
        )

        session.add(super_admin)
        session.commit()

        print("🎉 Admin user created successfully.")
