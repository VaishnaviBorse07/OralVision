from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError
from app.core.config import get_settings

settings = get_settings()


def _create_engine_with_fallback():
    try:
        eng = create_engine(settings.database_url)
        conn = eng.connect()
        conn.close()
        return eng
    except OperationalError:
        if settings.app_env == "development":
            sqlite_url = "sqlite:///./oralvision_dev.db"
            eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
            print(
                " PostgreSQL connection failed — falling back to SQLite at ./oralvision_dev.db"
            )
            return eng
        raise


engine = _create_engine_with_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from app.models import user, screening  # noqa: F401

    Base.metadata.create_all(bind=engine)
