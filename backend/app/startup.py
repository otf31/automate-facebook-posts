from sqlmodel import Session, select


from .config import settings
from .database import engine
from .models import RoleEnum, User


def create_super_admin_user():
    with Session(engine) as session:
        existing_admin = session.exec(
            select(User).where(User.role == RoleEnum.super_admin)  # noqa
        ).first()

        if existing_admin:
            print("Super admin user already exists.")
            return

        super_admin = User(
            user_id=settings.admin_id,
            machine_id=settings.admin_machine_id,
            role=RoleEnum.super_admin,
            comment="Мой компутер",
        )

        session.add(super_admin)
        session.commit()

        print("🎉 Admin user created successfully.")
