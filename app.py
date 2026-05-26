import streamlit as st

from core import auth
from core.state import inicializar_estado
from modulos.iso27701 import views as iso27701_views
from views import (
    action_plan,
    assessment,
    audit_log,
    dashboard,
    diagnosticos,
    history,
    home,
    login,
)

st.set_page_config(
    page_title="ISO/IEC 27000 - Diagnóstico de Conformidade",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
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
    "audit_log": audit_log.render,
    "login": login.render,
}


def _render_sidebar_usuario() -> None:
    """Mostra nome do logado e botão de sair na sidebar."""
    if auth.auth_desabilitada():
        st.sidebar.caption("Modo dev (autenticação desabilitada)")
        return

    nome = auth.usuario_logado_nome()
    email = auth.usuario_logado_email()
    if nome and email:
        st.sidebar.markdown(f"**{nome}**")
        st.sidebar.caption(email)
        cookie_secret = login._cookie_secret()  # noqa: SLF001 - reuso interno
        if cookie_secret:
            authenticator = auth.construir_authenticator(cookie_secret)
            authenticator.logout(button_name="Sair", location="sidebar", key="logout_sidebar")


# Gate: se a auth está ligada e o usuário não está logado, força a tela de login.
if not auth.auth_desabilitada() and auth.usuario_logado_email() is None:
    st.session_state.page = "login"

_render_sidebar_usuario()

ROTAS.get(st.session_state.page, home.render)()
