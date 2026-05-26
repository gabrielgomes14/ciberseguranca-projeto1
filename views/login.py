"""Tela de login e cadastro.

Usa `streamlit-authenticator` para o fluxo de login (com cookie persistente
de 30 dias) e nosso `core.auth.cadastrar` para o cadastro novo (gravando
direto no SQLite). O bypass `DIAGNOSTICO_AUTH=off` curto-circuita esta tela.
"""

import streamlit as st

from core import auth


def _cookie_secret() -> str | None:
    """Lê o segredo do cookie de st.secrets ou env, nessa ordem.

    Sem ele a sessão não persiste entre recargas. Em produção, configurar
    `[auth] cookie_secret = "..."` em `.streamlit/secrets.toml`.
    """
    try:
        return str(st.secrets["auth"]["cookie_secret"])
    except (KeyError, FileNotFoundError):
        import os

        return os.environ.get("DIAGNOSTICO_COOKIE_SECRET")


def render() -> None:
    if auth.auth_desabilitada():
        st.session_state.page = "home"
        st.rerun()
        return

    cookie_secret = _cookie_secret()
    if not cookie_secret:
        st.error(
            "Cookie secret não configurado. Defina `[auth] cookie_secret` em "
            "`.streamlit/secrets.toml` ou a variável de ambiente "
            "`DIAGNOSTICO_COOKIE_SECRET`."
        )
        st.code(
            'python -c "import secrets; print(secrets.token_urlsafe(32))"',
            language="bash",
        )
        return

    authenticator = auth.construir_authenticator(cookie_secret)

    aba_login, aba_cadastro = st.tabs(["Entrar", "Cadastrar"])

    with aba_login:
        authenticator.login(location="main", key="auth_login")

        status = st.session_state.get("authentication_status")
        if status is True:
            st.session_state.page = "home"
            st.rerun()
        elif status is False:
            st.error("Email ou senha incorretos.")
        elif status is None:
            st.info("Informe seu email e senha para continuar.")

    with aba_cadastro:
        st.markdown("Crie uma conta para começar a registrar diagnósticos.")
        with st.form("form_cadastro", clear_on_submit=False):
            nome = st.text_input("Nome completo", placeholder="João da Silva")
            email = st.text_input("Email", placeholder="joao@example.com")
            senha = st.text_input("Senha", type="password", help="Mínimo 8 caracteres")
            senha_conf = st.text_input("Confirmar senha", type="password")
            enviar = st.form_submit_button("Criar conta", type="primary")

        if enviar:
            if not nome.strip() or not email.strip() or not senha:
                st.error("Preencha todos os campos.")
            elif "@" not in email or "." not in email:
                st.error("Email inválido.")
            elif len(senha) < 8:
                st.error("A senha precisa ter pelo menos 8 caracteres.")
            elif senha != senha_conf:
                st.error("As senhas não conferem.")
            else:
                try:
                    auth.cadastrar(email.strip(), nome.strip(), senha)
                    st.success(
                        "Conta criada. Vá para a aba **Entrar** e use suas credenciais."
                    )
                except ValueError as e:
                    st.error(str(e))
