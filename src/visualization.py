import plotly.express as px
from datetime import timedelta

def plot_gantt(tasks, start_date):
    df = []
    for idx, t in enumerate(tasks):
        df.append({
            "Task": f"T{idx+1}",  # eje Y solo para separar filas
            "Start": start_date + timedelta(hours=t.start_time),
            "Finish": start_date + timedelta(hours=t.end_time),
            "Resource": getattr(t, "assigned_to", None),
            "Cliente": t.client,
            "Nombre completo": f"{t.client} - {t.name}"
        })

    # Ordenar por hora de inicio
    df.sort(key=lambda x: x["Start"])

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        hover_data=["Nombre completo", "Cliente"]
    )

    # Invertir eje Y para que lo primero quede arriba
    fig.update_yaxes(autorange="reversed", showticklabels=False)  # no mostrar etiquetas reales

    fig.update_layout(
        margin=dict(l=20, r=20, t=40, b=20),
        title="Gantt del proyecto",
        yaxis_title="",
        xaxis_title="Tiempo",
        height=max(300, len(tasks)*25)  # ajustar altura según número de tareas
    )

    return fig
