import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    # Check current version
    try:
        result = conn.execute(text("SELECT version_num FROM alembic_version"))
        rows = result.fetchall()
        print(f"Current alembic versions: {rows}")
    except Exception as e:
        print(f"No alembic_version table or error: {e}")

    # Clear it
    try:
        conn.execute(text("DELETE FROM alembic_version"))
        conn.commit()
        print("✓ Cleared alembic_version table")
    except Exception as e:
        print(f"Could not clear: {e}")

    # Stamp with our actual revision
    try:
        conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('610c39ee7fe6')"))
        conn.commit()
        print("✓ Stamped with 610c39ee7fe6")
    except Exception as e:
        print(f"Could not stamp: {e}")

    # Verify
    result = conn.execute(text("SELECT version_num FROM alembic_version"))
    print(f"Final version: {result.fetchall()}")
