"""Создание первого администратора через синхронную служебную сессию."""
from __future__ import annotations

from getpass import getpass

from sqlalchemy import select

from app.core.security import hash_password
from app.db.enums import UserRole
from app.db.models.user import User
from app.db.session import SessionLocal


def main() -> None:
    email = input("Email администратора: ").strip().lower()
    password = getpass("Пароль (минимум 8 символов): ")
    if len(password) < 8:
        raise SystemExit("Пароль слишком короткий")

    with SessionLocal() as session:
        existing = session.scalar(select(User).where(User.email == email))
        if existing:
            raise SystemExit("Пользователь с таким email уже существует")

        session.add(
            User(
                email=email,
                password_hash=hash_password(password),
                role=UserRole.ADMIN,
            )
        )
        session.commit()

    print("OK: администратор создан")


if __name__ == "__main__":
    main()
