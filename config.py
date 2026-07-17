# config.py
import os

try:
    from credenciales import *
except ImportError:
    # fallback si no existe el archivo (ej. en despliegue público)
    DB_NAME = os.getenv("LABORAL_DB", "nombre_de_tu_db")
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    CACHE_DIR = os.getenv("CACHE_DIR", "./cache")