import plotly.graph_objects as go

def kpis_diarios(df_kpis):
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_kpis["fecha"],
        y=df_kpis["new_users"],
        name="Nuevos usuarios"
    ))

    fig.add_trace(go.Scatter(
        x=df_kpis["fecha"],
        y=df_kpis["active_7d"],
        mode="lines+markers",
        name="Activos (7d)"
    ))

    fig.add_trace(go.Scatter(
        x=df_kpis["fecha"],
        y=df_kpis["payers"],
        mode="lines+markers",
        name="Pagadores"
    ))

    fig.add_trace(go.Bar(
        x=df_kpis["fecha"],
        y=df_kpis["payers_per_day"],
        name="Pagadores por día"
    ))

    fig.update_layout(
        title="📊 KPIs diarios — Laboral.AI (barras + líneas)",
        xaxis_title="Fecha",
        yaxis_title="Usuarios",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig

def funel_convercion(df_metricas):
    fig = go.Figure(go.Funnel(
        y = ["Usuarios Nuevos", "Usuarios Activos", "Usuarios Pagadores"],
        x = [
            df_metricas["new_users"].sum(),
            df_metricas["active_7d"].iloc[-1],
            df_metricas["payers_per_day"].sum()
        ],
        textinfo = "value+percent previous"
    ))
    fig.update_layout(title="Embudo de Conversión de Usuarios")

    return fig


def kpis_actividad(df_activities, graf=["cvs", "courses", "applications", "quizzes", "feedback", "chatbot"]):
    fig = go.Figure()

    if "cvs" in graf:
        fig.add_trace(go.Scatter(
            x=df_activities["fecha"],
            y=df_activities["cvs"],
            mode="lines+markers",
            name="CVs editados"
        ))

    if "courses" in graf:
            fig.add_trace(go.Scatter(
                x=df_activities["fecha"],
                y=df_activities["courses"],
                mode="lines+markers",
                name="Cursos inscritos"
            ))

    if "applications" in graf:
        fig.add_trace(go.Scatter(
            x=df_activities["fecha"],
            y=df_activities["applications"],
            mode="lines+markers",
            name="Postulaciones hechas"
        ))

    if "quizzes" in graf:
        fig.add_trace(go.Scatter(
            x=df_activities["fecha"],
            y=df_activities["quizzes"],
            mode="lines+markers",
            name="Quizzes completados"
        ))

    if "feedback" in graf:
        fig.add_trace(go.Scatter(
            x=df_activities["fecha"],
            y=df_activities["feedback"],
            mode="lines+markers",
            name="Feedback dados"
        ))

    if "chatbot" in graf:
        fig.add_trace(go.Scatter(
            x=df_activities["fecha"],
            y=df_activities["chatbot"],
            mode="lines+markers",
            name="Chatbot"
        ))

    fig.update_layout(
        title="📊 Actividades diarias por tipo — Laboral.AI (líneas)",
        xaxis_title="Fecha",
        yaxis_title="Usuarios",
        hovermode="x unified",
        template="plotly_white"
    )

    return fig