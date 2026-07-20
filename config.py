# config.py
import os
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME", "laboral-ai-dev")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
CACHE_DIR = os.getenv("CACHE_DIR", "./cache")