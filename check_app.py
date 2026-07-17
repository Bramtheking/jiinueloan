import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(__file__))

# Load env first
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
    print("✓ dotenv loaded")
except Exception as e:
    print(f"✗ dotenv failed: {e}")

# Try importing the app
try:
    from app.main import app as fastapi_app
    print("✓ app imported successfully")
except Exception as e:
    print(f"✗ app import failed:")
    traceback.print_exc()
    sys.exit(1)

# Try wrapping with a2wsgi
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(fastapi_app)
    print("✓ ASGIMiddleware wrapping OK")
except Exception as e:
    print(f"✗ ASGIMiddleware failed: {e}")
    traceback.print_exc()

print("\nAll checks done.")
