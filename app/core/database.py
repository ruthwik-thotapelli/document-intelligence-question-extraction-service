from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from .config import settings

# SQLite needs special connect_args; PostgreSQL doesn't
connect_args = {}
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    connect_args=connect_args,
)

# Enable WAL mode on SQLite for better concurrency
if settings.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
