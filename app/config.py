import os

from typing import Optional

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////data/app.db")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
