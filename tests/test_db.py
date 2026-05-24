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


def test_criar_e_carregar_diagnostico(db_path: str) -> None:
    from core.db import carregar_avaliacoes, criar_diagnostico, init_db, salvar_avaliacoes
    init_db()
    did = criar_diagnostico("iso27001", "Acme Ltda.", data_auditoria="2026-05-10")
    assert did > 0

    salvar_avaliacoes(did, {
        "5.1": Avaliacao(status="Conforme", criticidade="Alta", observacao="ok"),
        "5.2": Avaliacao(status="Parcial", responsavel="João"),
        "5.3": Avaliacao(status="Não Conforme", remediacao="Sim"),
    })
    av = carregar_avaliacoes(did)
    assert av["5.1"].status == "Conforme"
    assert av["5.1"].criticidade == "Alta"
    assert av["5.2"].responsavel == "João"
    assert av["5.3"].remediacao == "Sim"


def test_diagnostico_guarda_data_auditoria(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_diagnosticos
    init_db()
    criar_diagnostico("iso27001", "Acme", data_auditoria="2026-04-30")
    diag = listar_diagnosticos("iso27001")[0]
    assert diag.data_auditoria == "2026-04-30"


def test_data_auditoria_default_hoje(db_path: str) -> None:
    from datetime import date

    from core.db import criar_diagnostico, init_db, listar_diagnosticos
    init_db()
    criar_diagnostico("iso27001", "X")
    diag = listar_diagnosticos("iso27001")[0]
    assert diag.data_auditoria == date.today().isoformat()


def test_listar_diagnosticos_filtra_por_modulo(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_diagnosticos
    init_db()
    criar_diagnostico("iso27001", "A")
    criar_diagnostico("iso27701", "B")
    criar_diagnostico("iso27001", "C")
    assert len(listar_diagnosticos("iso27001")) == 2
    assert len(listar_diagnosticos("iso27701")) == 1
    assert len(listar_diagnosticos()) == 3


def test_snapshots(db_path: str) -> None:
    from core.db import criar_diagnostico, init_db, listar_snapshots, salvar_snapshot
    init_db()
    did = criar_diagnostico("iso27001", "Acme")
    salvar_snapshot(did, "baseline", 75.0, {"4": 80.0, "5": 70.0}, 10)
    salvar_snapshot(did, "Q2", 82.5, {"4": 85.0, "5": 80.0}, 12)
    snaps = listar_snapshots(did)
    assert len(snaps) == 2
    assert snaps[0].rotulo == "baseline"
    assert snaps[1].score_geral == 82.5
    assert snaps[1].scores_por_categoria["4"] == 85.0


def test_excluir_cascateia(db_path: str) -> None:
    from core.db import (
        carregar_avaliacoes,
        criar_diagnostico,
        excluir_diagnostico,
        init_db,
        listar_snapshots,
        salvar_avaliacoes,
        salvar_snapshot,
    )
    init_db()
    did = criar_diagnostico("iso27001", "X")
    salvar_avaliacoes(did, {"5.1": Avaliacao(status="Conforme")})
    salvar_snapshot(did, "s", 100.0, {"org": 100.0}, 1)
    excluir_diagnostico(did)
    assert carregar_avaliacoes(did) == {}
    assert listar_snapshots(did) == []
