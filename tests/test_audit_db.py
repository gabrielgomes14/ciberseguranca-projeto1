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


def test_registrar_evento_simples(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    eid = registrar_evento("teste.acao")
    assert eid > 0

    eventos = listar_eventos()
    assert len(eventos) == 1
    e = eventos[0]
    assert e.id == eid
    assert e.acao == "teste.acao"
    assert e.usuario_email is None
    assert e.alvo_tipo is None
    assert e.alvo_id is None
    assert e.detalhes == {}
    assert e.quando  # ISO 8601 não vazio


def test_registrar_evento_completo(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    registrar_evento(
        "diagnostico.criado",
        usuario_email="auditor@example.com",
        alvo_tipo="diagnostico",
        alvo_id="42",
        detalhes={"modulo": "iso27001", "organizacao": "Acme"},
    )
    e = listar_eventos()[0]
    assert e.usuario_email == "auditor@example.com"
    assert e.alvo_tipo == "diagnostico"
    assert e.alvo_id == "42"
    assert e.detalhes == {"modulo": "iso27001", "organizacao": "Acme"}


def test_listar_eventos_ordenado_desc(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    for i in range(3):
        registrar_evento(f"acao.{i}")
    eventos = listar_eventos()
    # Mais recente primeiro: como o timestamp tem precisão de segundos,
    # usamos id DESC como tiebreaker (já implementado no ORDER BY).
    assert [e.acao for e in eventos] == ["acao.2", "acao.1", "acao.0"]


def test_listar_eventos_filtra_por_acao(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    registrar_evento("diagnostico.criado")
    registrar_evento("snapshot.criado")
    registrar_evento("diagnostico.criado")

    so_diag = listar_eventos(acao="diagnostico.criado")
    assert len(so_diag) == 2
    assert all(e.acao == "diagnostico.criado" for e in so_diag)


def test_listar_eventos_filtra_por_alvo(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    registrar_evento("diagnostico.criado", alvo_tipo="diagnostico", alvo_id="1")
    registrar_evento("diagnostico.criado", alvo_tipo="diagnostico", alvo_id="2")
    registrar_evento("snapshot.criado", alvo_tipo="snapshot", alvo_id="1")

    diag = listar_eventos(alvo_tipo="diagnostico")
    assert len(diag) == 2

    diag_2 = listar_eventos(alvo_tipo="diagnostico", alvo_id="2")
    assert len(diag_2) == 1
    assert diag_2[0].alvo_id == "2"


def test_listar_eventos_filtra_por_usuario(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    registrar_evento("a", usuario_email="alice@example.com")
    registrar_evento("b", usuario_email="bob@example.com")
    registrar_evento("c", usuario_email="alice@example.com")

    alice = listar_eventos(usuario_email="alice@example.com")
    assert len(alice) == 2


def test_listar_eventos_respeita_limite(db_path: str) -> None:
    from core.db import init_db, listar_eventos, registrar_evento
    init_db()
    for i in range(10):
        registrar_evento(f"acao.{i}")
    assert len(listar_eventos(limite=5)) == 5


def test_detalhes_invalidos_nao_quebram_listagem(db_path: str) -> None:
    """Se um JSON inválido foi gravado direto no banco (corrupção), listar não pode falhar."""
    from core.db import conexao, init_db, listar_eventos
    init_db()
    with conexao() as con:
        con.execute(
            "INSERT INTO audit_log (quando, acao, detalhes) VALUES (?, ?, ?)",
            ("2026-05-25T12:00:00", "teste", "{not json"),
        )
    eventos = listar_eventos()
    assert len(eventos) == 1
    assert eventos[0].detalhes == {}
