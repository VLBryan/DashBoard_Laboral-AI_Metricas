# Laboral.AI — Dashboard de Métricas

Dashboard interactivo desarrollado en **Streamlit** para visualizar KPIs de usuarios, actividad y chatbot en la plataforma **Laboral.AI**.  
Integra datos desde **MongoDB** y genera gráficos dinámicos con **Plotly**.

---

## Características principales
- **KPIs diarios**: nuevos usuarios, activos, pagadores.
- **Actividad general**: CVs editados, cursos inscritos, postulaciones, quizzes, feedback y uso del chatbot.
- **Chatbot insights**:
  - Histograma de mensajes por conversación.
  - Top intents más frecuentes.
  - Tasa de handoff (derivación a humano).
- **Filtros de fechas** en el sidebar (últimos 7 días, 30 días, 3 meses, 1 año, completo).
- **Cache local** para optimizar carga de datos.

---

## Tecnologías usadas
- [Python](ca://s?q=Python) (pandas, datetime, pymongo)
- [Streamlit](ca://s?q=Streamlit)
- [Plotly](ca://s?q=Plotly)
- [MongoDB](ca://s?q=MongoDB)

---

## Estructura del proyecto

```text
├── app.py                # Aplicación principal Streamlit
├── src/
│   ├── cargar_datos.py   # Funciones ETL y cache
│   ├── grafico_metricas.py
│   ├── grafico_chatbot.py
├── cache/                # Archivos CSV cacheados
└── README.md             # Este archivo
```

---

## ⚡ Instalación y uso
1. Clonar el repositorio:
```bash
git clone https://github.com/tuusuario/LaboralAI-Dashboard.git
cd LaboralAI-Dashboard
```
2. Crear entorno virtual e instalar dependencias:
```bash
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
export MONGO_URI="mongodb://localhost:27017"
export DB_NAME="laboral_ai"
```

4. Ejecutar el dashboard:
```bash
streamlit run app.py
```

---

## Autor
Desarrollado por Bryan Villasante López  
Practicante de Data Science & Analytics en Laboral.AI