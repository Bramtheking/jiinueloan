import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

from app.config import settings
from sqlalchemy import create_engine, text

engine = create_engine(settings.database_url)
db_user = "wykqfeio_wykqfeio"

with engine.connect() as conn:
    # Find sequences via pg_class
    sequences = conn.execute(text(
        "SELECT relname FROM pg_class WHERE relkind = 'S'"
    )).fetchall()
    print(f"Found {len(sequences)} sequences via pg_class")

    for (seq_name,) in sequences:
        try:
            conn.execute(text(f'GRANT USAGE, SELECT, UPDATE ON SEQUENCE "{seq_name}" TO "{db_user}"'))
            print(f"✓ {seq_name}")
        except Exception as e:
            print(f"✗ {seq_name}: {e}")

    conn.commit()
    print("Done.")
