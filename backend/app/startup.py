import secrets
import string

from sqlmodel import Session, func, select

from .config import settings
from .database import engine
from .models import Admin
from .security import get_password_hash


def generate_password(length=8):
    alphabet = string.ascii_letters + string.digits

    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_super_admin_user():
    with Session(engine) as session:
        exists_admin = session.exec(select(func.count()).select_from(Admin)).one()

        if exists_admin:
            print("Super admin user already exists")
            return

        temp_super_admin_password = generate_password()

        super_admin = Admin(
            admin_id=settings.super_admin_id,
            password=get_password_hash(temp_super_admin_password),
        )

        session.add(super_admin)
        session.commit()

        print(f"""
        Super admin created successfully
        Temporal super admin password: {temp_super_admin_password}
        """)
