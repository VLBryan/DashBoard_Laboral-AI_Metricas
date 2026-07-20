import streamlit as st
import pandas as pd
from datetime import timedelta, datetime
from dateutil.relativedelta import relativedelta

from config import *
from src.cargar_datos import build_all, load_df_cache
from src.grafico_metricas import kpis_diarios, funel_convercion, kpis_actividad
from src.grafico_chatbot import histograma_mensajes, top_intents, tasa_handoff

# -------------------------
# Config
# -------------------------
st.set_page_config(layout="wide", page_title="Laboral.AI - Dashboard Metricas")

# -------------------------
# Data loading (cached)
# -------------------------
@st.cache_data(ttl=600)
def load_data_cached(db_name: str, mongo_uri: str):
    metricas_path = os.path.join(CACHE_DIR, "df_metricas.csv")
    actividad_path = os.path.join(CACHE_DIR, "df_actividad.csv")
    chatbot_path = os.path.join(CACHE_DIR, "df_chatbot.csv")
    chatbot_msgs_per_conv_path = os.path.join(CACHE_DIR, "df_chatbot_msgs_per_conv.csv")
    chatbot_top_intents_path = os.path.join(CACHE_DIR, "df_chatbot_top_intents.csv")
    handoff_path = os.path.join(CACHE_DIR, "df_handoff.csv")

    try:
        # Intentar cargar cache local
        if os.path.exists(metricas_path) and os.path.exists(actividad_path) and os.path.exists(chatbot_path):
            df_metricas = load_df_cache(metricas_path)
            df_actividad = load_df_cache(actividad_path)
            df_chatbot = load_df_cache(chatbot_path, con_fecha=False)
            df_chatbot_msgs_per_conv = load_df_cache(chatbot_msgs_per_conv_path, con_fecha=False)
            df_chatbot_top_intents = load_df_cache(chatbot_top_intents_path, con_fecha=False)
            df_handoff = load_df_cache(handoff_path, con_fecha=False)
            return {"df_metricas": df_metricas, 
                    "df_actividad": df_actividad,
                    "df_chatbot": df_chatbot,
                    "df_chatbot_msgs_per_conv": df_chatbot_msgs_per_conv,
                    "df_chatbot_top_intents": df_chatbot_top_intents,
                    "df_handoff": df_handoff}
    except Exception as e:
        st.warning(f"No se pudo leer cache local: {e}")

    # Si no hay cache o falla → recalcular desde Mongo
    try:
        return build_all(db_name, mongo_uri, cache_dir=CACHE_DIR)
    except Exception as e:
        st.error(f"Error al cargar datos desde Mongo: {e}")
        return {"df_metricas": pd.DataFrame(), 
                "df_actividad": pd.DataFrame(),
                "df_chatbot": pd.DataFrame(),
                "df_chatbot_msgs_per_conv": pd.DataFrame(),
                "df_chatbot_top_intents": pd.DataFrame(),
                "df_handoff": pd.DataFrame()}


# Uso en tu app
data_bundle = load_data_cached(DB_NAME, MONGO_URI)
df_metricas = data_bundle["df_metricas"]
df_actividad = data_bundle["df_actividad"]
df_chatbot = data_bundle["df_chatbot"]
df_chatbot_msgs_per_conv = data_bundle["df_chatbot_msgs_per_conv"]
df_chatbot_top_intents = data_bundle["df_chatbot_top_intents"]
df_handoff = data_bundle["df_handoff"]

# -------------------------
# Sidebar: filtros globales
# -------------------------
st.sidebar.header("Filtro de fechas")

# Valores iniciales (todo el rango disponible)
fecha_inicio = df_metricas["fecha"].min().date()
fecha_fin = df_metricas["fecha"].max().date()

# Botones rápidos para setear rangos
hoy = datetime.utcnow().date()

if st.sidebar.button("Últimos 7 días"):
    fecha_inicio = hoy - timedelta(days=7)
    fecha_fin = hoy

if st.sidebar.button("Últimos 30 días"):
    fecha_inicio = hoy - timedelta(days=30)
    fecha_fin = hoy

if st.sidebar.button("Últimos 3 meses"):
    fecha_inicio = hoy - relativedelta(months=3)
    fecha_fin = hoy

if st.sidebar.button("Último año"):
    fecha_inicio = hoy - relativedelta(years=1)
    fecha_fin = hoy

if st.sidebar.button("Completo"):
    fecha_inicio = df_metricas["fecha"].min().date()
    fecha_fin = df_metricas["fecha"].max().date()

# Inputs manuales (por si el usuario quiere ajustar)
fecha_inicio = st.sidebar.date_input("Fecha inicio", fecha_inicio)
fecha_fin = st.sidebar.date_input("Fecha fin", fecha_fin)

# Botón de recarga de cache (opcional)
if st.sidebar.button("Forzar recarga datos (ETL)"):
    load_data_cached.clear()
    data_bundle = build_all(DB_NAME, MONGO_URI, cache_dir=CACHE_DIR)
    df_metricas = data_bundle["df_metricas"]
    df_actividad = data_bundle["df_actividad"]
    df_chatbot = data_bundle["df_chatbot"]
    df_chatbot_msgs_per_conv = data_bundle["df_chatbot_msgs_per_conv"]
    df_chatbot_top_intents = data_bundle["df_chatbot_top_intents"]
    df_handoff = data_bundle["df_handoff"]
    st.sidebar.success("Datos recargados")


# Filtrar DataFrame según rango
df_filtrado_metricas = df_metricas[(df_metricas["fecha"].dt.date >= fecha_inicio) & (df_metricas["fecha"].dt.date <= fecha_fin)]
df_filtrado_actividad = df_actividad[(df_actividad["fecha"].dt.date >= fecha_inicio) & (df_actividad["fecha"].dt.date <= fecha_fin)]

# -------------------------
# --- Título ---
# -------------------------
st.title("Dashboard de KPIs — Laboral.AI")

st.markdown("---")

# --- KPIs ---
col1, col2, col3 = st.columns(3)
col1.metric(label="Usuarios Nuevos", 
            value=df_metricas["new_users"].sum(), 
            delta=df_filtrado_metricas["new_users"].iloc[-1])
col2.metric(label="Usuarios Activos", 
            value=df_metricas["active_7d"].iloc[-1], 
            delta=df_filtrado_metricas["active_7d"].iloc[-1] - df_filtrado_metricas["active_7d"].iloc[-2])
col3.metric(label="Usuarios Pagadores", 
            value=df_metricas["payers_per_day"].sum(), 
            delta=df_filtrado_metricas["payers_per_day"].iloc[-1])

st.markdown("---")

st.plotly_chart(funel_convercion(df_filtrado_metricas), use_container_width=True)

st.plotly_chart(kpis_diarios(df_filtrado_metricas), use_container_width=True)

st.markdown("---")

col4, col5, col6 = st.columns(3)
col4.metric(label="CVs editados", 
            value=df_filtrado_actividad["cvs"].sum(), 
            delta=df_filtrado_actividad["cvs"].iloc[-1])
col5.metric(label="Cursos inscritos", 
            value=df_filtrado_actividad["courses"].sum(), 
            delta=df_filtrado_actividad["courses"].iloc[-1])
col6.metric(label="Postulaciones", 
            value=df_filtrado_actividad["applications"].sum(), 
            delta=df_filtrado_actividad["applications"].iloc[-1])

col7, col8, col9 = st.columns(3)
col7.metric(label="Quizzes completados", 
            value=df_filtrado_actividad["quizzes"].sum(), 
            delta=df_filtrado_actividad["quizzes"].iloc[-1])
col8.metric(label="Feedback dado", 
            value=df_filtrado_actividad["feedback"].sum(), 
            delta=df_filtrado_actividad["feedback"].iloc[-1])
col9.metric(label="Chatbot", 
            value=df_filtrado_actividad["chatbot"].sum(), 
            delta=df_filtrado_actividad["chatbot"].iloc[-1])

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    ["General", "CVs editados", "Cursos inscritos", "Postulaciones hechas", 
     "Quizzes completados", "Feedback dados", "Chatbot"])

with tab1:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad), use_container_width=True)

with tab2:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["cvs"]), use_container_width=True)

with tab3:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["courses"]), use_container_width=True)

with tab4:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["applications"]), use_container_width=True)
    
with tab5:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["quizzes"]), use_container_width=True)
    
with tab6:
    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["feedback"]), use_container_width=True)

with tab7:

    col10, col11, col12 = st.columns(3)
    col10.metric(label="Conversaciones Unicas", 
                value=df_chatbot["total_convs"])
    col11.metric(label="Usuarios únicos", 
                value=df_chatbot["unique_users"])
    col12.metric(label="Promedio de mensajes por conversacion", 
                value=df_chatbot_msgs_per_conv.mean().round(1))

    st.plotly_chart(kpis_actividad(df_filtrado_actividad, graf=["chatbot"]), use_container_width=True)


    st.plotly_chart(histograma_mensajes(df_chatbot_msgs_per_conv), use_container_width=True)
    st.plotly_chart(top_intents(df_chatbot_top_intents), use_container_width=True)
    st.plotly_chart(tasa_handoff(df_handoff["porcentaje"]), use_container_width=True)



