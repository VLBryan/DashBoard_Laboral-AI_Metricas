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

def load_df_cache(path: str, con_fecha=True) -> pd.DataFrame:
    df = pd.read_csv(path, index_col=False)
    if con_fecha:
        df["fecha"] = pd.to_datetime(df["fecha"])
    return df


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

    # -------------------------
    # df de Métricas generales
    # -------------------------
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

    # -------------------------
    # df de Actividad general
    # -------------------------
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

    # -------------------------
    # df de Chatbot específico
    # -------------------------
    aiconv = pd.DataFrame(list(db.aiconversations.find({}, {"user": 1, "requiresHuman": 1, "status": 1})))
    aimsg = pd.DataFrame(list(db.aimessages.find({}, {"user": 1, "conversation": 1, "intent": 1})))

    if not aiconv.empty and not aimsg.empty:
        total_convs = len(aiconv)
        unique_users = aiconv['user'].nunique()
        total_msgs = len(aimsg)
        df_chatbot_msgs_per_conv = aimsg.groupby('conversation').size().rename('msgs_count')
        df_chatbot_top_intents = aimsg['intent'].value_counts().head(20).reset_index()
        df_chatbot_top_intents.columns = ['intent','count']
        df_handoff = aiconv['requiresHuman'].value_counts(normalize=True).mul(100).round(2).reset_index()
        df_handoff.columns = ["requiresHuman", "porcentaje"]

        df_chatbot = pd.DataFrame({
            "total_convs": [total_convs],
            "unique_users": [unique_users],
            "total_msgs": [total_msgs]
        })
    else:
        df_chatbot = pd.DataFrame()


    # -------------------------
    # Guardar en cache
    # -------------------------
    os.makedirs(cache_dir, exist_ok=True)
    save_df_cache(df_metricas, os.path.join(cache_dir, "df_metricas.csv"))
    save_df_cache(df_actividad, os.path.join(cache_dir, "df_actividad.csv"))
    save_df_cache(df_chatbot, os.path.join(cache_dir, "df_chatbot.csv"))
    save_df_cache(df_chatbot_msgs_per_conv, os.path.join(cache_dir, "df_chatbot_msgs_per_conv.csv"))
    save_df_cache(df_chatbot_top_intents, os.path.join(cache_dir, "df_chatbot_top_intents.csv"))
    save_df_cache(df_handoff, os.path.join(cache_dir, "df_handoff.csv"))
    
    return {
        "df_metricas": df_metricas,
        "df_actividad": df_actividad,
        "df_chatbot": df_chatbot,
        "df_chatbot_msgs_per_conv": df_chatbot_msgs_per_conv,
        "df_chatbot_top_intents": df_chatbot_top_intents,
        "df_handoff": df_handoff
    }

