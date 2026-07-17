import os
from typing import List, Dict, Optional
import pandas as pd
from datetime import timedelta, datetime
from pymongo import MongoClient

# Intentamos importar ObjectId para detectar y convertirlo
try:
    from bson import ObjectId
except Exception:
    ObjectId = None

# -------------------------
# Configuración / Conexión
# -------------------------
def get_mongo_client(uri: Optional[str] = None) -> MongoClient:
    uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
    return MongoClient(uri)

def get_collection_df(client: MongoClient, db_name: str, coll_name: str) -> pd.DataFrame:
    db = client[db_name]
    cursor = db[coll_name].find()
    df = pd.DataFrame(list(cursor))
    return df

# -------------------------
# Cargas
# -------------------------
def load_collections(client: MongoClient, db_name: str, collections: List[str]) -> Dict[str, pd.DataFrame]:
    out = {}
    for c in collections:
        try:
            out[c] = get_collection_df(client, db_name, c)
        except Exception as e:
            print(f"Warning: no se pudo cargar {c}: {e}")
            out[c] = pd.DataFrame()
    return out

# -------------------------
# Funciones KPI (lectura)
# -------------------------

def new_users(db, fecha):
    # contar usuarios creados ese día
    inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=1)
    return db.users.count_documents({"createdAt": {"$gte": inicio, "$lt": fin}})

def active_count(db, fecha, days=7):
    since = fecha - timedelta(days=days)

    cvs_ids = set(doc["_id"] for doc in db.cvs.aggregate([
        {"$match": {"updatedAt": {"$gte": since, "$lt": fecha}}},
        {"$group": {"_id": "$user"}}
    ]))

    course_ids = set(doc["_id"] for doc in db.courseenrollments.aggregate([
        {"$match": {"createdAt": {"$gte": since, "$lt": fecha}}},
        {"$group": {"_id": "$user"}}
    ]))

    quiz_ids = set(doc["_id"] for doc in db.quizresults.aggregate([
        {"$match": {"createdAt": {"$gte": since, "$lt": fecha}}},
        {"$group": {"_id": "$user"}}
    ]))

    feedback_ids = set(doc["_id"] for doc in db.employabilities.aggregate([
        {"$match": {"updatedAt": {"$gte": since, "$lt": fecha}, "feedback": {"$exists": True}}},
        {"$group": {"_id": "$user"}}
    ]))

    application_ids = set(doc["_id"] for doc in db.applications.aggregate([
        {"$match": {"createdAt": {"$gte": since, "$lt": fecha}}},
        {"$group": {"_id": "$user"}}
    ]))

    chatbot_ids = set(doc["_id"] for doc in db.aiconversations.aggregate([
        {"$match": {"createdAt": {"$gte": since, "$lt": fecha}}},
        {"$group": {"_id": "$user"}}
    ]))

    return len(cvs_ids.union(course_ids, quiz_ids, feedback_ids, application_ids, chatbot_ids))

def payers_count(db, fecha):
    return db.payments.count_documents({"status": "approved", "createdAt": {"$lte": fecha}})

def payers_per_day(db, fecha):
    inicio = fecha.replace(hour=0, minute=0, second=0, microsecond=0)
    fin = inicio + timedelta(days=1)
    return db.payments.count_documents({
        "status": "approved",
        "createdAt": {"$gte": inicio, "$lt": fin}
    })

# -------------------------
# Cache / persistencia simple
# -------------------------
def save_df_cache(df: pd.DataFrame, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

def load_df_cache(path: str) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["fecha"])

# -------------------------
# Construimos build_all
# -------------------------
def build_all(db_name: str, mongo_uri: Optional[str] = None, cache_dir: str = "./cache") -> Dict[str, pd.DataFrame]:
    client = get_mongo_client(mongo_uri)
    db = client[db_name]

    # Rango desde el primer registro hasta hoy
    min_fecha = datetime(2024, 8, 12)  # Fecha mínima fija (primer registro conocido)
    hoy = datetime.utcnow()  # Fecha máxima = hoy

    fechas = pd.date_range(start=min_fecha, end=hoy, freq="D")

    # df de Metricas
    data = []
    for f in fechas:
        row = {
            "fecha": f,
            "new_users": new_users(db, f),
            "active_7d": active_count(db, f, 7),
            "payers": payers_count(db, f),
            "payers_per_day": payers_per_day(db, f)
        }
        data.append(row)

    df_metricas = pd.DataFrame(data)

    # df de Actividad
    data = []
    for f in fechas:
        row = {
            "fecha": f,
            "cvs": db.cvs.count_documents({"updatedAt": {"$gte": f, "$lt": f + timedelta(days=1)}}),
            "courses": db.courseenrollments.count_documents({"createdAt": {"$gte": f, "$lt": f + timedelta(days=1)}}),
            "applications": db.applications.count_documents({"createdAt": {"$gte": f, "$lt": f + timedelta(days=1)}}),
            "quizzes": db.quizresults.count_documents({"createdAt": {"$gte": f, "$lt": f + timedelta(days=1)}}),
            "feedback": db.employabilities.count_documents({"updatedAt": {"$gte": f, "$lt": f + timedelta(days=1)}, "feedback": {"$exists": True}}),
            "chatbot": db.aiconversations.count_documents({"createdAt": {"$gte": f, "$lt": f + timedelta(days=1)}})
        }
        data.append(row)

    df_actividad = pd.DataFrame(data)

    os.makedirs(cache_dir, exist_ok=True)
    save_df_cache(df_metricas, os.path.join(cache_dir, "df_metricas.csv"))
    save_df_cache(df_actividad, os.path.join(cache_dir, "df_actividad.csv"))

    return {"df_metricas": df_metricas, "df_actividad": df_actividad}