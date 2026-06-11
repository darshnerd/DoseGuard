from sqlmodel import Session, SQLModel, create_engine

from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False},
)


def init_db():
    from app import models  # noqa: F401

    SQLModel.metadata.create_all(engine)
    _run_light_migrations()


def _run_light_migrations():
    from sqlalchemy import text

    with engine.begin() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(user)"))}
        if "timezone" not in cols:
            conn.execute(
                text('ALTER TABLE "user" ADD COLUMN timezone VARCHAR DEFAULT \'Asia/Kolkata\'')
            )


def get_session():
    with Session(engine) as session:
        yield session