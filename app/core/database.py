from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./focusflow.db")

# For development, use SQLite if PostgreSQL not available
if DATABASE_URL.startswith("postgresql://") and "localhost" in DATABASE_URL:
    try:
        engine = create_engine(DATABASE_URL)
        engine.connect()
    except Exception:
        # Fallback to SQLite for development
        DATABASE_URL = "sqlite:///./focusflow.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()