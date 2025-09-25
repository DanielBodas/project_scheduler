# pages/1_visualizacion.py
import streamlit as st
import yaml
from datetime import datetime, timedelta
from src.process_manager import build_processes
from src.scheduler import Scheduler
from src.visualization import plot_gantt
from src.models import Person

CONFIG_FILE = "config.yaml"

def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

st.set_page_config(page_title="Visualización Gantt", layout="wide")
st.title("📈 Visualización del Gantt")

config = load_config()

# Fecha de inicio
raw_start = config.get("start_day")
if isinstance(raw_start, str):
    start_date = datetime.fromisoformat(raw_start)
else:
    start_date = raw_start

# Botón para recalcular Gantt
if st.button("🚀 Calcular Gantt"):
    # Construir procesos
    processes, global_last_map = build_processes(config)

    # Crear pool de personas y servidores
    people = [Person("Ana"), Person("Luis")]
    servers = {"S1": 0.0, "S2": 0.0}

    # Ejecutar scheduler
    sched = Scheduler(people, servers, start_day=start_date)
    tasks = sched.schedule(processes)

    # Mostrar Gantt
    st.subheader("📈 Gantt")
    plot_gantt(tasks, start_date)

    # Tabla de resultados
    st.subheader("📋 Tabla de tareas")
    data = []
    for t in tasks:
        data.append({
            "Cliente": t.client,
            "Tarea": t.name,
            "Asignado a": getattr(t, "assigned_to", None),
            "Inicio": start_date + timedelta(hours=t.start_time),
            "Fin": start_date + timedelta(hours=t.end_time),
            "Prioridad": t.priority
        })
    st.dataframe(data)
