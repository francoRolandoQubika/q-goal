"""
Central config — loads .env and exposes typed settings.
Import this before any other internal module that needs env vars.
"""
from pathlib import Path
from dotenv import load_dotenv
import os

DATA_DIR: Path = Path(__file__).parents[3]  # genai/ root

load_dotenv(DATA_DIR / ".env")

OPENAI_API_KEY: str = os.environ.get("OPENAI_API_KEY", "")
STATS_PDF:      str = os.environ.get("STATS_PDF", str(DATA_DIR / "statsFifa.pdf"))
API_PORT:       int = int(os.environ.get("API_PORT", "8002"))
