import os
from typing import Dict, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool


def _default_database_url() -> str:
    """Compose the default Postgres connection string."""
    host = os.getenv("DB_HOST", "postgres.production.svc.cluster.local")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "flowengine_db")
    user = os.getenv("DB_USER", "flowengine_user")
    password = os.getenv("DB_PASSWORD", "changeme")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = os.getenv("DATABASE_URL", _default_database_url())

engine_kwargs: Dict[str, Any] = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine_kwargs["connect_args"] = connect_args
    if DATABASE_URL.endswith(":memory:"):
        engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db() -> None:
    """Create database tables if they do not exist."""
    Base.metadata.create_all(bind=engine)
