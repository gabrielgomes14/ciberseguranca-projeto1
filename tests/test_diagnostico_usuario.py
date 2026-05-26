"""Testes do vínculo entre diagnóstico e usuário."""

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


def test_criar_diagnostico_persiste_email(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_diagnosticos

    init_db()
    did = criar_diagnostico(
        "iso27001", "Acme", usuario_email="alice@example.com"
    )
    diags = listar_diagnosticos()
    assert len(diags) == 1
    assert diags[0].id == did
    assert diags[0].usuario_email == "alice@example.com"


def test_email_normalizado_lowercase(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_diagnosticos

    init_db()
    criar_diagnostico("iso27001", "Acme", usuario_email="  Alice@Example.COM  ")
    assert listar_diagnosticos()[0].usuario_email == "alice@example.com"


def test_listar_filtra_por_usuario_e_inclui_publicos(db_path: str) -> None:
    """Diagnósticos sem dono (NULL) aparecem para qualquer usuário logado."""
    from core.db import criar_diagnostico, init_db, listar_diagnosticos

    init_db()
    criar_diagnostico("iso27001", "Sem dono")  # usuario_email = NULL
    criar_diagnostico("iso27001", "Da Alice", usuario_email="alice@example.com")
    criar_diagnostico("iso27001", "Do Bob", usuario_email="bob@example.com")

    da_alice = listar_diagnosticos(usuario_email="alice@example.com")
    orgs = {d.organizacao for d in da_alice}
    assert orgs == {"Sem dono", "Da Alice"}

    do_bob = listar_diagnosticos(usuario_email="bob@example.com")
    orgs = {d.organizacao for d in do_bob}
    assert orgs == {"Sem dono", "Do Bob"}


def test_listar_sem_filtro_retorna_tudo(db_path: str) -> None:
    """Sem usuario_email (ex.: bypass dev), retorna todos os diagnósticos."""
    from core.db import criar_diagnostico, init_db, listar_diagnosticos

    init_db()
    criar_diagnostico("iso27001", "A", usuario_email="alice@example.com")
    criar_diagnostico("iso27001", "B", usuario_email="bob@example.com")
    criar_diagnostico("iso27001", "C")

    assert len(listar_diagnosticos()) == 3


def test_listar_filtra_por_modulo_e_usuario(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_diagnosticos

    init_db()
    criar_diagnostico("iso27001", "A1", usuario_email="alice@example.com")
    criar_diagnostico("iso27701", "A2", usuario_email="alice@example.com")
    criar_diagnostico("iso27001", "B1", usuario_email="bob@example.com")

    da_alice_27001 = listar_diagnosticos(
        "iso27001", usuario_email="alice@example.com"
    )
    assert len(da_alice_27001) == 1
    assert da_alice_27001[0].organizacao == "A1"
