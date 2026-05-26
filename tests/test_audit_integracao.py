"""Verifica que as operações principais de core.db registram eventos no audit_log."""

import os
import tempfile

import pytest

from core.models import Avaliacao


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


def test_criar_diagnostico_registra_evento(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_eventos

    init_db()
    did = criar_diagnostico("iso27001", "Acme")

    eventos = listar_eventos(acao="diagnostico.criado")
    assert len(eventos) == 1
    e = eventos[0]
    assert e.alvo_tipo == "diagnostico"
    assert e.alvo_id == str(did)
    assert e.detalhes["modulo"] == "iso27001"
    assert e.detalhes["organizacao"] == "Acme"


def test_atualizar_diagnostico_registra_evento(db_path: str) -> None:
    from core.db import atualizar_diagnostico, criar_diagnostico, init_db, listar_eventos

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    atualizar_diagnostico(did, "Acme S/A", "2026-05-01")

    eventos = listar_eventos(acao="diagnostico.atualizado")
    assert len(eventos) == 1
    assert eventos[0].alvo_id == str(did)
    assert eventos[0].detalhes["organizacao"] == "Acme S/A"


def test_excluir_diagnostico_registra_evento(db_path: str) -> None:
    from core.db import criar_diagnostico, excluir_diagnostico, init_db, listar_eventos

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    excluir_diagnostico(did)

    eventos = listar_eventos(acao="diagnostico.excluido")
    assert len(eventos) == 1
    assert eventos[0].alvo_id == str(did)


def test_salvar_avaliacoes_registra_evento(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_eventos, salvar_avaliacoes

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    salvar_avaliacoes(did, {
        "5.1": Avaliacao(status="Conforme"),
        "5.2": Avaliacao(status="Não Conforme"),
    })

    eventos = listar_eventos(acao="avaliacoes.salvas")
    assert len(eventos) == 1
    e = eventos[0]
    assert e.alvo_id == str(did)
    assert e.detalhes["total"] == 2
    por_status = e.detalhes["por_status"]
    assert isinstance(por_status, dict)
    assert por_status["Conforme"] == 1
    assert por_status["Não Conforme"] == 1


def test_salvar_snapshot_registra_evento(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_eventos, salvar_snapshot

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    sid = salvar_snapshot(did, "v1", 75.0, {"5": 80.0}, 10)

    eventos = listar_eventos(acao="snapshot.criado")
    assert len(eventos) == 1
    e = eventos[0]
    assert e.alvo_id == str(sid)
    assert e.detalhes["score_geral"] == 75.0
    assert e.detalhes["avaliados"] == 10
    assert e.detalhes["rotulo"] == "v1"


def test_excluir_snapshot_registra_evento(db_path: str) -> None:
    from core.db import (
        criar_diagnostico,
        excluir_snapshot,
        init_db,
        listar_eventos,
        salvar_snapshot,
    )

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    sid = salvar_snapshot(did, "v1", 75.0, {}, 0)
    excluir_snapshot(sid)

    eventos = listar_eventos(acao="snapshot.excluido")
    assert len(eventos) == 1
    assert eventos[0].alvo_id == str(sid)


def test_fluxo_completo_gera_sequencia_de_eventos(db_path: str) -> None:
    """Cenário: cria, salva avaliações, snapshota, exclui. Espera 5 eventos."""
    from core.db import (
        criar_diagnostico,
        excluir_diagnostico,
        init_db,
        listar_eventos,
        salvar_avaliacoes,
        salvar_snapshot,
    )

    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    salvar_avaliacoes(did, {"5.1": Avaliacao(status="Conforme")})
    salvar_snapshot(did, "v1", 100.0, {}, 1)
    excluir_diagnostico(did)

    eventos = listar_eventos()
    acoes = [e.acao for e in eventos]
    # ordem desc: o mais recente primeiro
    assert acoes == [
        "diagnostico.excluido",
        "snapshot.criado",
        "avaliacoes.salvas",
        "diagnostico.criado",
    ]
