import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# PostgreSQL Configuration
DB_USER = os.getenv("DB_USER", "st")
DB_PASSWORD = os.getenv("DB_PASSWORD", "st")
DB_HOST = os.getenv("DB_HOST", "192.168.1.10")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "st")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
SQLITE_URL = "sqlite:///exoplanets.db"

# Default Engine (Postgres)
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_session_factory(mode="PostgreSQL"):
    """Returns a sessionmaker bound to the requested database engine."""
    if mode == "SQLite":
        # Check Same Thread must be false for Streamlit
        sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
        return sessionmaker(autocommit=False, autoflush=False, bind=sqlite_engine)
    else:
        return SessionLocal