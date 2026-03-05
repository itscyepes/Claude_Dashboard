from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./sessions.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def init_db():
    import models  # noqa: F401 — ensures models are registered before create_all
    Base.metadata.create_all(bind=engine)
    # Add last_seen_at column to existing DBs that pre-date the column
    from sqlalchemy import text
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE sessions ADD COLUMN last_seen_at DATETIME"))
            conn.commit()
        except Exception:
            pass  # Column already exists


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
