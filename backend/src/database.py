""" #src/database.py
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create the database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class for ORM models
Base = declarative_base()

# Dependency to get the database session
def get_db_session():
    #Provide a database session for dependency injection.
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Run Alembic migrations
def run_migrations():
    #Run Alembic migrations automatically.
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

# Initialize the database
def init_db():
    #Initialize the database by creating all tables and applying migrations.
    try:
        # Run Alembic migrations
        run_migrations()
        print("Database initialized and migrations applied successfully.")
    except SQLAlchemyError as e:
        print(f"Error initializing the database: {e}")
        raise """

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable not set")

# Create the database engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class for ORM models
Base = declarative_base()

# Dependency to get the database session
def get_db_session():
    """Provide a database session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize the database
def init_db():
    """Initialize the database by creating all tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except SQLAlchemyError as e:
        print(f"Error initializing the database: {e}")
        raise