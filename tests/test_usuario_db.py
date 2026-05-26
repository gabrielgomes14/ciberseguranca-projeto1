"""Testes do CRUD de usuário em core.db."""

import os
import tempfile

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


def test_criar_e_buscar_usuario(db_path: str) -> None:
    from core.db import buscar_usuario, criar_usuario, init_db

    init_db()
    criar_usuario("alice@example.com", "Alice", "hash$alice")

    u = buscar_usuario("alice@example.com")
    assert u is not None
    assert u.email == "alice@example.com"
    assert u.nome == "Alice"
    assert u.senha_hash == "hash$alice"
    assert u.ativo is True
    assert u.criado_em  # ISO 8601 não vazio


def test_email_normalizado_para_lowercase(db_path: str) -> None:
    from core.db import buscar_usuario, criar_usuario, init_db

    init_db()
    criar_usuario("  Alice@Example.COM  ", "Alice", "h")

    assert buscar_usuario("alice@example.com") is not None
    assert buscar_usuario("ALICE@EXAMPLE.COM") is not None
    assert buscar_usuario("  alice@example.com  ") is not None


def test_email_duplicado_levanta(db_path: str) -> None:
    from core.db import criar_usuario, init_db

    init_db()
    criar_usuario("alice@example.com", "Alice", "h1")
    with pytest.raises(ValueError, match="já cadastrado"):
        criar_usuario("alice@example.com", "Outra Alice", "h2")


def test_listar_usuarios_ordena_por_criado_em(db_path: str) -> None:
    from core.db import criar_usuario, init_db, listar_usuarios

    init_db()
    criar_usuario("a@x.com", "A", "h")
    criar_usuario("b@x.com", "B", "h")
    criar_usuario("c@x.com", "C", "h")

    emails = [u.email for u in listar_usuarios()]
    assert emails == ["a@x.com", "b@x.com", "c@x.com"]


def test_buscar_usuario_inexistente_retorna_none(db_path: str) -> None:
    from core.db import buscar_usuario, init_db

    init_db()
    assert buscar_usuario("nada@example.com") is None


def test_atualizar_senha_usuario(db_path: str) -> None:
    from core.db import atualizar_senha_usuario, buscar_usuario, criar_usuario, init_db

    init_db()
    criar_usuario("alice@example.com", "Alice", "old_hash")
    atualizar_senha_usuario("alice@example.com", "new_hash")

    u = buscar_usuario("alice@example.com")
    assert u is not None
    assert u.senha_hash == "new_hash"
