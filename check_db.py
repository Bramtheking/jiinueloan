import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

url = os.environ.get("DATABASE_URL", "NOT SET")
# Mask password for display
import re
masked = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', url)
print(f"DATABASE_URL: {masked}")

# Try connecting
try:
    from sqlalchemy import create_engine, text
    engine = create_engine(url)
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("✓ DB connection successful")
except Exception as e:
    print(f"✗ DB connection failed: {e}")
