from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, scoped_session

DATABASE_URL = "sqlite:///./mini_crm.db"

# Engine erzeugt die Verbindung zur Datenbank
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True
)

SessionLocal = scoped_session(
    sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        future=True
    )
)

Base = declarative_base()
