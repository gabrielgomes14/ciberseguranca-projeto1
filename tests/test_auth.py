"""Testes unitários dos helpers de autenticação."""

import os
import tempfile
from unittest.mock import patch

import pytest


@pytest.fixture
def db_path() -> object:
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(path)
    os.environ["DIAGNOSTICO_DB_PATH"] = path
    os.environ["DIAGNOSTICO_SEED_DEMO"] = "0"
    yield path
    if os.path.exists(path):
        os.remove(path)
    os.environ.pop("DIAGNOSTICO_DB_PATH", None)
    os.environ.pop("DIAGNOSTICO_SEED_DEMO", None)
    os.environ.pop("DIAGNOSTICO_AUTH", None)


def test_auth_desabilitada_default() -> None:
    from core.auth import auth_desabilitada

    os.environ.pop("DIAGNOSTICO_AUTH", None)
    assert auth_desabilitada() is False


def test_auth_desabilitada_off() -> None:
    from core.auth import auth_desabilitada

    os.environ["DIAGNOSTICO_AUTH"] = "off"
    assert auth_desabilitada() is True

    os.environ["DIAGNOSTICO_AUTH"] = "OFF"
    assert auth_desabilitada() is True


def test_auth_desabilitada_outro_valor() -> None:
    from core.auth import auth_desabilitada

    os.environ["DIAGNOSTICO_AUTH"] = "on"
    assert auth_desabilitada() is False


def test_hash_senha_gera_bcrypt() -> None:
    from core.auth import hash_senha

    h = hash_senha("minha_senha_forte")
    # bcrypt: 60 chars começando com $2b$
    assert h.startswith("$2b$")
    assert len(h) == 60


def test_hash_senhas_diferentes_dao_hashes_diferentes() -> None:
    from core.auth import hash_senha

    assert hash_senha("a") != hash_senha("b")


def test_carregar_credenciais_vazio(db_path: str) -> None:
    from core.auth import carregar_credenciais
    from core.db import init_db

    init_db()
    creds = carregar_credenciais()
    assert creds == {"usernames": {}}


def test_carregar_credenciais_com_usuarios(db_path: str) -> None:
    from core.auth import carregar_credenciais
    from core.db import criar_usuario, init_db

    init_db()
    criar_usuario("alice@example.com", "Alice", "hash$alice")
    criar_usuario("bob@example.com", "Bob", "hash$bob")

    creds = carregar_credenciais()
    assert set(creds["usernames"].keys()) == {"alice@example.com", "bob@example.com"}
    alice = creds["usernames"]["alice@example.com"]
    assert alice["name"] == "Alice"
    assert alice["password"] == "hash$alice"


def test_cadastrar_persiste_e_hasha(db_path: str) -> None:
    from core.auth import cadastrar
    from core.db import buscar_usuario, init_db

    init_db()
    cadastrar("alice@example.com", "Alice", "senha123")

    u = buscar_usuario("alice@example.com")
    assert u is not None
    assert u.nome == "Alice"
    assert u.senha_hash.startswith("$2b$")  # foi hashada
    assert u.senha_hash != "senha123"


def test_usuario_logado_email_bypass() -> None:
    from core.auth import usuario_logado_email

    os.environ["DIAGNOSTICO_AUTH"] = "off"
    assert usuario_logado_email() == "dev@local"


def test_usuario_logado_nome_bypass() -> None:
    from core.auth import usuario_logado_nome

    os.environ["DIAGNOSTICO_AUTH"] = "off"
    assert usuario_logado_nome() == "Desenvolvedor"


def test_usuario_logado_email_sem_sessao() -> None:
    """Sem bypass e sem session_state válido, retorna None."""
    from core import auth

    os.environ.pop("DIAGNOSTICO_AUTH", None)
    fake_st = type("FakeSt", (), {"session_state": {}})()
    with patch.dict("sys.modules", {"streamlit": fake_st}):
        assert auth.usuario_logado_email() is None
