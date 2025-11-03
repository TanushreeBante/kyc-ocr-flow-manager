from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os
load_dotenv()

# -----------------------------------------------------------------------------
# DATABASE CONFIGURATION
# -----------------------------------------------------------------------------

# Use environment variable if available, else fallback to SQLite for testing


DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

# Create SessionLocal for DB interactions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()

# -----------------------------------------------------------------------------
# DATABASE DEPENDENCY
# -----------------------------------------------------------------------------
def get_db():
    """
    Dependency for FastAPI routes.
    Opens a new database session per request and closes it automatically.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
