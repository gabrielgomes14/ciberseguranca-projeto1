"""Autenticação multi-usuário sobre `streamlit-authenticator` com SQLite.

A biblioteca espera um dicionário `credentials` em memória; mantemos esse
dicionário como projeção da tabela `usuario`. O cadastro e a redefinição de
senha gravam direto no banco via `core.db`, evitando o YAML padrão da lib (que
não funciona bem em ambientes read-only como o Streamlit Cloud).

Bypass para desenvolvimento e testes: `DIAGNOSTICO_AUTH=off` desabilita o gate
e retorna um usuário fictício (`dev@local`).
"""

import os
from typing import TYPE_CHECKING, Any

from core import db

if TYPE_CHECKING:  # evita custo de import no startup quando bypass está ligado
    import streamlit_authenticator as stauth

_USUARIO_DEV = db.Usuario(
    email="dev@local",
    nome="Desenvolvedor",
    senha_hash="",
    criado_em="",
    ativo=True,
)


def auth_desabilitada() -> bool:
    """Retorna True quando a autenticação está desligada via env var."""
    return os.environ.get("DIAGNOSTICO_AUTH", "").lower() == "off"


def carregar_credenciais() -> dict[str, dict[str, dict[str, Any]]]:
    """Monta o dicionário esperado pela `Authenticate` a partir do banco.

    Formato:
    ``{"usernames": {email: {"name": ..., "email": ..., "password": hash}}}``
    """
    usuarios = db.listar_usuarios(somente_ativos=True)
    return {
        "usernames": {
            u.email: {
                "name": u.nome,
                "email": u.email,
                "password": u.senha_hash,
                "failed_login_attempts": 0,
                "logged_in": False,
            }
            for u in usuarios
        }
    }


def construir_authenticator(cookie_secret: str) -> "stauth.Authenticate":
    """Cria a instância de `Authenticate` configurada com backend SQLite.

    `auto_hash=False` porque já gravamos hashes no banco - se a lib re-hashar,
    invalida as senhas. `cookie_secret` é a chave de assinatura do cookie de
    sessão (ler de `st.secrets["auth"]["cookie_secret"]`).
    """
    import streamlit_authenticator as stauth

    return stauth.Authenticate(
        credentials=carregar_credenciais(),
        cookie_name="diagnostico_iso_auth",
        cookie_key=cookie_secret,
        cookie_expiry_days=30.0,
        auto_hash=False,
    )


def hash_senha(senha: str) -> str:
    """Gera hash bcrypt no mesmo formato que a lib usa internamente."""
    import streamlit_authenticator as stauth

    fake_creds: dict[str, dict[str, Any]] = {
        "usernames": {"_": {"name": "_", "email": "_", "password": senha}}
    }
    hashed = stauth.Hasher.hash_passwords(fake_creds)
    return str(hashed["usernames"]["_"]["password"])


def cadastrar(email: str, nome: str, senha: str) -> None:
    """Cria um novo usuário com senha em texto puro - o hash é feito aqui."""
    db.criar_usuario(email=email, nome=nome, senha_hash=hash_senha(senha))


def usuario_logado_email() -> str | None:
    """Retorna o email do usuário logado, ou None.

    Quando o bypass está ativo (`DIAGNOSTICO_AUTH=off`), retorna o email do
    usuário fictício `dev@local` para compatibilidade com o restante do código
    (audit log, vínculo de diagnósticos).
    """
    if auth_desabilitada():
        return _USUARIO_DEV.email

    import streamlit as st

    if st.session_state.get("authentication_status") is True:
        username = st.session_state.get("username")
        return str(username) if username else None
    return None


def usuario_logado_nome() -> str | None:
    """Retorna o nome do usuário logado, ou None."""
    if auth_desabilitada():
        return _USUARIO_DEV.nome

    import streamlit as st

    if st.session_state.get("authentication_status") is True:
        nome = st.session_state.get("name")
        return str(nome) if nome else None
    return None
