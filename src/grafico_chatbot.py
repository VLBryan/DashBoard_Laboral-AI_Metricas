import plotly.graph_objects as go
import plotly.express as px

def histograma_mensajes(df_chatbot_msgs_per_conv, nbins=30):
    fig = px.histogram(
        df_chatbot_msgs_per_conv,
        x='msgs_count',
        nbins=nbins,
        title='Mensajes por conversación',
        labels={'msgs_count':'Mensajes','count':'Frecuencia'}
    )

    fig.update_layout(
        xaxis_title='Mensajes',
        yaxis_title='Frecuencia',
        hovermode='x unified',
        bargap=0.05
    )

    # Traducción de hover y leyenda
    fig.update_traces(
        hovertemplate='Mensajes: %{x}<br>Frecuencia: %{y}<extra></extra>'
    )

    return fig

def top_intents(df_chatbot_top_intents):
    fig = px.bar(
        df_chatbot_top_intents,
        x='intent',
        y='count',
        title='Intenciones más frecuentes',
        labels={'intent':'Intención','count':'Frecuencia'}
    )

    fig.update_layout(
        xaxis_title='Intención',
        yaxis_title='Frecuencia',
        hovermode='x unified'
    )

    fig.update_traces(
        hovertemplate='Intención: %{x}<br>Frecuencia: %{y}<extra></extra>'
    )

    return fig

def tasa_handoff(handoff):
    fig = px.pie(
        values=handoff.values,
        names=handoff.index.map(lambda x: "Requiere humano" if x else "Resuelto por bot"),
        title="Tasa de derivación a atención humana (%)",
        labels={"names": "Tipo de conversación", "values": "Porcentaje"}
    )

    fig.update_traces(
        textinfo="label+percent",
        hovertemplate="%{label}: %{percent:.1%}<extra></extra>"
    )

    fig.update_layout(
        legend_title="Resultado",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig
