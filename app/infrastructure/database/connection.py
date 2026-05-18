import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://ledger:ledger@localhost:5432/ledger_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session]:
    with session_factory() as session:
        yield session
