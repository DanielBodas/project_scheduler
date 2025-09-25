import streamlit as st
import yaml
from datetime import datetime, timedelta
from src.process_manager import build_processes
from src.scheduler import Scheduler
from src.visualization import plot_gantt  # función que devuelve figura Plotly
from src.models import Person

CONFIG_FILE = "config.yaml"

# -------------------------
# Configuración de página
# -------------------------
st.set_page_config(page_title="Visualización Gantt", layout="wide")
st.title("📈 Gantt del proyecto")

# -------------------------
# Sidebar: selección de personas
# -------------------------
st.sidebar.header("Configuración de personas")
num_people = st.sidebar.number_input(
    "Número de personas en el proyecto", min_value=1, max_value=20, value=2, step=1
)

people_names = []
for i in range(num_people):
    name = st.sidebar.text_input(f"Nombre persona {i+1}", value=f"Persona_{i+1}")
    people_names.append(name)

people = [Person(name) for name in people_names]

# -------------------------
# Cargar configuración YAML
# -------------------------
def load_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

config = load_config()

raw_start = config.get("start_day")
if isinstance(raw_start, str):
    start_date = datetime.fromisoformat(raw_start)
else:
    start_date = raw_start

# -------------------------
# Construir procesos y scheduler
# -------------------------
processes, global_last_map = build_processes(config)

servers = {"S1": 0.0, "S2": 0.0}  # dos servidores
sched = Scheduler(people, servers, start_day=start_date)
tasks = sched.schedule(processes)

# -------------------------
# Mostrar Gantt
# -------------------------
fig = plot_gantt(tasks, start_date)
st.plotly_chart(fig, use_container_width=True)

# -------------------------
# Tabla de resultados
# -------------------------
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
