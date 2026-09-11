from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# This is the connection string: it tells SQLAlchemy how to reach our PostgreSQL database.
# Format: postgresql://<username>:<password>@<host>:<port>/<database_name>
DATABASE_URL = "postgresql://postgres:pgsql123@localhost:5432/medibridge"

# The "engine" is the core object that manages the actual connection to the database.
engine = create_engine(DATABASE_URL)

# SessionLocal is a factory that creates new "database sessions" — 
# a session is like a temporary workspace for talking to the database
# (e.g. "add this row", "get all users") before saving (committing) the changes.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is a special class that all our future database tables (models) will inherit from.
# It lets SQLAlchemy know "this Python class represents a database table."
Base = declarative_base()