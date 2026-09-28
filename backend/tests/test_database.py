import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.models.user import User
from app.utils.enums import UserRole


def test_create_and_read_user_sqlite() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = session_factory()
    try:
        user = User(
            name="Sqlite User",
            email="sqlite.user@example.com",
            password_hash="not-a-real-hash",
            role=UserRole.VERIFIER,
            is_active=True,
            is_verified=False,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        loaded = session.get(User, user.id)
        assert loaded is not None
        assert isinstance(loaded.id, uuid.UUID)
        assert loaded.email == "sqlite.user@example.com"
        assert loaded.role == UserRole.VERIFIER
    finally:
        session.close()
        engine.dispose()


def test_postgres_connection(db_engine: Engine) -> None:
    with db_engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        assert result.scalar_one() == 1


def test_create_and_read_user(db_session: Session) -> None:
    user = User(
        name="Test User",
        email="test.user@example.com",
        password_hash="not-a-real-hash",
        role=UserRole.USER,
        is_active=True,
        is_verified=False,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    loaded = db_session.get(User, user.id)

    assert loaded is not None
    assert isinstance(loaded.id, uuid.UUID)
    assert loaded.email == "test.user@example.com"
    assert loaded.role == UserRole.USER
    assert loaded.is_active is True
    assert loaded.is_verified is False
    assert loaded.created_at is not None
    assert loaded.created_at.tzinfo is not None
    assert loaded.created_at.astimezone(timezone.utc)
    assert isinstance(loaded.updated_at, datetime)
