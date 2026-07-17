import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.database_url)

with engine.connect() as conn:
    current = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    print(f"Before: {current}")

    conn.execute(text("DELETE FROM alembic_version"))
    conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('610c39ee7fe6')"))
    conn.commit()

    current = conn.execute(text("SELECT version_num FROM alembic_version")).fetchall()
    print(f"After: {current}")

print("Done.")
