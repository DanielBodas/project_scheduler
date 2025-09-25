# archivo: Home.py (o el main de Streamlit)
import streamlit as st

# Configuración general de la app
st.set_page_config(
    page_title="Project Scheduler",
    page_icon="📅",
    layout="wide"
)

# --- Portada ---
st.title("📅 Project Scheduler")
st.subheader("Organiza tus proyectos y tareas de manera simple y visual")

st.markdown("---")

# Métricas rápidas (ejemplo)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Proyectos activos", 3)
with col2:
    st.metric("Tareas pendientes", 12)
with col3:
    st.metric("Próxima entrega", "5 días")

st.markdown("---")

# Mensaje de bienvenida
st.success("Usa el menú lateral para navegar entre las secciones del scheduler.")
