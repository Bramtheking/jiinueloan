import os
from dotenv import load_dotenv

# Load .env file if it exists (local dev). On Render the var is injected directly.
load_dotenv()


class Settings:
    database_url: str = os.environ["DATABASE_URL"]


settings = Settings()
