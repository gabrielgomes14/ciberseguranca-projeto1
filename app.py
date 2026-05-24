import streamlit as st

from core.state import inicializar_estado
from modulos.iso27701 import views as iso27701_views
from views import action_plan, assessment, dashboard, diagnosticos, history, home

st.set_page_config(
    page_title="ISO/IEC 27000 - Diagnóstico de Conformidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """<style>
    .stButton > button { border-radius: 8px; font-weight: 500; }
    .stProgress > div > div > div { background-color: #1d4ed8; }
    </style>""",
    unsafe_allow_html=True,
)

inicializar_estado()

ROTAS = {
    "home": home.render,
    "diagnosticos": diagnosticos.render,
    "iso27001_assessment": assessment.render,
    "iso27001_dashboard": dashboard.render,
    "iso27001_action_plan": action_plan.render,
    "iso27701_assessment": iso27701_views.render_assessment,
    "iso27701_dashboard": iso27701_views.render_dashboard,
    "history": history.render,
}
ROTAS.get(st.session_state.page, home.render)()
