import streamlit as st

from core.state import inicializar_estado
from modulos.iso27701 import views as iso27701_views
from views import action_plan, assessment, dashboard, diagnosticos, history, home

_THEMES = {
    "light": {
        "primary": "#1d4ed8",
        "background": "#f8fafc",
        "secondary": "#f1f5f9",
        "text": "#0f172a",
    },
    "dark": {
        "primary": "#60a5fa",
        "background": "#0b1220",
        "secondary": "#111827",
        "text": "#e5e7eb",
    },
}


def _apply_theme(theme_name: str) -> None:
    theme = _THEMES.get(theme_name, _THEMES["dark"])
    st.markdown(
        f"""<style>
        :root {{
            --primary-color: {theme['primary']};
            --background-color: {theme['background']};
            --secondary-background-color: {theme['secondary']};
            --text-color: {theme['text']};
        }}
        .stApp {{
            background-color: var(--background-color);
            color: var(--text-color);
        }}
        section[data-testid="stSidebar"] {{
            background-color: var(--secondary-background-color);
        }}
        .stButton > button {{
            border-radius: 8px;
            font-weight: 500;
        }}
        .stProgress > div > div > div {{
            background-color: var(--primary-color);
        }}
        </style>""",
        unsafe_allow_html=True,
    )


def _render_theme_toggle() -> None:
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"
    if st.sidebar.button("Alternar tema"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
    tema_label = "Escuro" if st.session_state.theme == "dark" else "Claro"
    st.sidebar.caption(f"Tema atual: {tema_label}")

st.set_page_config(
    page_title="ISO/IEC 27000 — Diagnóstico de Conformidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

_render_theme_toggle()
_apply_theme(st.session_state.theme)

inicializar_estado()

ROTAS = {
    "home": home.render,
    "diagnosticos": diagnosticos.render,
    "iso27002_assessment": assessment.render,
    "iso27002_dashboard": dashboard.render,
    "iso27002_action_plan": action_plan.render,
    "iso27701_assessment": iso27701_views.render_assessment,
    "iso27701_dashboard": iso27701_views.render_dashboard,
    "history": history.render,
}
ROTAS.get(st.session_state.page, home.render)()
